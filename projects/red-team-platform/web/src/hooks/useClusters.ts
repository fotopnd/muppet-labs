import { useQuery } from '@tanstack/react-query'
import type { ClusterMembersOut, ClustersOut } from '@/types'

const API = import.meta.env['VITE_API_URL'] ?? 'http://localhost:8003'

export function useClusters() {
  return useQuery<ClustersOut>({
    queryKey: ['clusters'],
    queryFn: () => fetch(`${API}/clusters`).then((r) => r.json()),
  })
}

export function useClusterMembers(clusterId: number | null) {
  return useQuery<ClusterMembersOut>({
    queryKey: ['clusterMembers', clusterId],
    queryFn: () => fetch(`${API}/clusters/${clusterId}/members`).then((r) => r.json()),
    enabled: clusterId !== null,
  })
}
