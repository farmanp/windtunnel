import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/Layout';
import { RunListPage, RunDetailPage, InstanceTimelinePage, ErrorPage, SystemPage, ScenarioVisualizerPage } from '@/pages';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
});

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    errorElement: <ErrorPage />,
    children: [
      {
        index: true,
        element: <RunListPage />,
      },
      {
        path: 'runs/:runId',
        element: <RunDetailPage />,
      },
      {
        path: 'runs/:runId/instances/:instanceId',
        element: <InstanceTimelinePage />,
      },
      {
        path: 'scenarios',
        element: <ScenarioVisualizerPage />,
      },
      {
        path: 'settings',
        element: <SystemPage />,
      },
    ],
  },
]);

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>
  );
}

export default App;
