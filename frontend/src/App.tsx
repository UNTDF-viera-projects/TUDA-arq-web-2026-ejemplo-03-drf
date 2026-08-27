import { Suspense, use, useEffect, useRef, useState } from 'react'
import './App.css'


function App() {
  return (
    <main>
      <h1>Vite + React + TypeScript</h1>
      <p>Frontend conectado con Django a través de use().</p>
      <h1>Cons suspense</h1>
      <Suspense fallback={<p>Cargando actividades...</p>}>
        <ActivitiesListSuspense promise={activitiesPromise} />
      </Suspense>
      <h1>Con useEffect</h1>
      <ActivitiesList />
    </main>
  )
}

function ActivitiesList() {
  const [activities, setActivities] = useState<Activity[]>([])
  const [isFetching, setIsFetching] = useState(true)
  const [isError, setIsError] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const isMountedRef = useRef(true)
  const isSuccess = !isFetching && !isError

  useEffect(() => {
    isMountedRef.current = true

    fetchActivities()
      .then((data) => {
        if (isMountedRef.current) {
          setActivities(data)
        }
      })
      .catch((error) => {
        if (isMountedRef.current) {
          setIsError(true)
          setErrorMessage(error instanceof Error ? error.message : 'Error desconocido')
        }
        console.error('Error al obtener las actividades:', error)
      })
      .finally(() => {
        if (isMountedRef.current) {
          setIsFetching(false)
        }
      })

    return () => {
      isMountedRef.current = false
    }
  }, [])

  if (isFetching) {
    return <p>Cargando actividades...</p>
  }

  if (isError) {
    return <p>Error al cargar actividades: {errorMessage}</p>
  }

  if (isSuccess && activities.length === 0) {
    return <p>No hay actividades cargadas.</p>
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Título</th>
            <th scope="col">Comienza</th>
            <th scope="col">Capacidad</th>
            <th scope="col">Cupos disponibles</th>
          </tr>
        </thead>
        <tbody>
          {activities.map((activity) => (
            <tr key={activity.id}>
              <td><code>{activity.id}</code></td>
              <td>{activity.title}</td>
              <td>
                <time dateTime={activity.starts_at}>
                  {new Date(activity.starts_at).toISOString()}
                </time>
              </td>
              <td>{activity.capacity}</td>
              <td>{activity.available_slots}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

interface Activity {
  id: string
  title: string
  starts_at: string
  capacity: number
  available_slots: number
}

async function fetchActivities(): Promise<Activity[]> {
  const response = await fetch('/api/v1/activities')
  if (!response.ok) {
    throw new Error('Error al obtener las actividades')
  }
  return response.json()
}

// --------------------------------------------------
// --------------------------------------------------
// --------------------------------------------------

const activitiesPromise = fetchActivities()

function ActivitiesListSuspense({ promise }: { promise: Promise<Activity[]> }) {
  const activities = use(promise)

  if (activities.length === 0) {
    return <p>No hay actividades cargadas.</p>
  }

  return (
    <div className="table-container">
      <table>
        <thead>
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Título</th>
            <th scope="col">Comienza</th>
            <th scope="col">Capacidad</th>
            <th scope="col">Cupos disponibles</th>
          </tr>
        </thead>
        <tbody>
          {activities.map((activity) => (
            <tr key={activity.id}>
              <td><code>{activity.id}</code></td>
              <td>{activity.title}</td>
              <td>
                <time dateTime={activity.starts_at}>
                  {new Date(activity.starts_at).toISOString()}
                </time>
              </td>
              <td>{activity.capacity}</td>
              <td>{activity.available_slots}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App
