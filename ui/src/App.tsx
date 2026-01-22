import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from '@/components/Layout';
import { RunListPage } from '@/pages/RunListPage';
import { RunDetailPage } from '@/pages/RunDetailPage';
import { InstanceTimelinePage } from '@/pages/InstanceTimelinePage';

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
