import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ingestionApi } from '@/services/api'
import { format } from 'date-fns'
import { fmtFileSize } from '@/utils/format'
import type { SourceType } from '@/types'

const SOURCE_TYPES: { value: SourceType; label: string; icon: string; description: string; color: string }[] = [
  {
    value: 'sap_fuel', label: 'SAP Fuel / Procurement', icon: '⛽',
    description: 'SAP ECC/S4HANA fuel, diesel & gas exports with multilingual headers',
    color: 'border-amber-300 bg-amber-50 hover:border-amber-400 hover:bg-amber-100',
  },
  {
    value: 'utility_electricity', label: 'Utility Electricity', icon: '⚡',
    description: 'Smart meter and utility billing exports (kWh/MWh)',
    color: 'border-ocean-300 bg-ocean-50 hover:border-ocean-400 hover:bg-ocean-100',
  },
  {
    value: 'corporate_travel', label: 'Corporate Travel', icon: '✈️',
    description: 'Concur / Navan travel expense exports (flights, hotels, rail)',
    color: 'border-teal-300 bg-teal-50 hover:border-teal-400 hover:bg-teal-100',
  },
]

const FILE_STATUS_STYLE: Record<string, { badge: string; dot: string }> = {
  pending:    { badge: 'badge-pending',    dot: 'bg-amber-400 animate-pulse' },
  processing: { badge: 'badge-processing', dot: 'bg-ocean-400 animate-pulse' },
  processed:  { badge: 'badge-approved',   dot: 'bg-teal-500' },
  failed:     { badge: 'badge-flagged',    dot: 'bg-red-500' },
}

export default function UploadCenterPage() {
  const [selectedType, setSelectedType] = useState<SourceType>('sap_fuel')
  const [successMsg, setSuccessMsg]     = useState<string | null>(null)
  const qc = useQueryClient()

  const { data: uploadsRes, isLoading } = useQuery({
    queryKey: ['source-files'],
    queryFn: () => ingestionApi.list(),
    refetchInterval: 6000,
  })

  const uploadMutation = useMutation({
    mutationFn: ({ file }: { file: File }) => ingestionApi.upload(file, selectedType),
    onSuccess: (res) => {
      setSuccessMsg(res.data.data?.original_filename || 'File')
      qc.invalidateQueries({ queryKey: ['source-files'] })
      setTimeout(() => setSuccessMsg(null), 6000)
    },
  })

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) uploadMutation.mutate({ file: accepted[0] })
  }, [selectedType])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'text/csv': ['.csv'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024,
  })

  const uploads = uploadsRes?.data?.data || []

  return (
    <div className="space-y-6 animate-fade-in max-w-5xl">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Upload Center</h1>
        <p className="text-slate-500 text-sm mt-1">Ingest ESG data from SAP, utilities, and travel systems</p>
      </div>

      {/* Source type selector */}
      <div className="card p-5">
        <div className="text-xs font-bold text-ocean-700 uppercase tracking-wider mb-4">1 — Select Data Source Type</div>
        <div className="grid grid-cols-3 gap-3">
          {SOURCE_TYPES.map((st) => (
            <button
              key={st.value}
              onClick={() => setSelectedType(st.value)}
              className={`p-4 rounded-2xl border-2 text-left transition-all duration-200 ${
                selectedType === st.value
                  ? `${st.color} ring-2 ring-offset-1 ring-ocean-400 shadow-md`
                  : `${st.color}`
              }`}
            >
              <div className="text-3xl mb-2">{st.icon}</div>
              <div className="text-sm font-bold text-slate-800 mb-1">{st.label}</div>
              <div className="text-xs text-slate-500 leading-relaxed">{st.description}</div>
              {selectedType === st.value && (
                <div className="mt-2 text-xs font-bold text-ocean-600">✓ Selected</div>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Drop zone */}
      <div className="card p-3">
        <div className="text-xs font-bold text-ocean-700 uppercase tracking-wider mb-3 px-2">2 — Upload File</div>
        <div
          {...getRootProps()}
          className={`rounded-2xl border-2 border-dashed p-12 text-center cursor-pointer transition-all duration-300 ${
            isDragActive
              ? 'border-ocean-400 bg-ocean-50'
              : uploadMutation.isPending
                ? 'border-amber-300 bg-amber-50'
                : 'border-ocean-200 bg-sand-50 hover:border-ocean-400 hover:bg-ocean-50'
          }`}
        >
          <input {...getInputProps()} />
          {uploadMutation.isPending ? (
            <div className="flex flex-col items-center gap-3">
              <div className="w-12 h-12 border-2 border-ocean-200 border-t-ocean-500 rounded-full animate-spin" />
              <p className="text-slate-700 font-semibold">Processing your file...</p>
              <p className="text-slate-400 text-sm">Parsing rows and detecting anomalies</p>
            </div>
          ) : isDragActive ? (
            <div className="flex flex-col items-center gap-2">
              <div className="text-5xl animate-bounce">📂</div>
              <p className="text-ocean-700 font-bold text-lg">Release to upload</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <div className="w-16 h-16 rounded-2xl bg-ocean-100 flex items-center justify-center text-3xl animate-wave">
                ☁️
              </div>
              <div>
                <p className="text-slate-700 font-bold text-base">Drag & drop your file here</p>
                <p className="text-slate-400 text-sm mt-1">or click to browse — CSV, XLSX up to 50 MB</p>
              </div>
              <button type="button" className="btn-primary mt-1">Browse Files</button>
            </div>
          )}
        </div>
      </div>

      {/* Feedback */}
      {successMsg && (
        <div className="alert-success">
          <span className="text-xl flex-shrink-0">✅</span>
          <div>
            <div className="font-bold">{successMsg} uploaded!</div>
            <div className="text-sm mt-0.5">Queued for ingestion — processing in background. Refresh in a few seconds.</div>
          </div>
        </div>
      )}
      {uploadMutation.isError && (
        <div className="alert-error">
          <span className="text-xl flex-shrink-0">❌</span>
          <div>
            <div className="font-bold">Upload failed</div>
            <div className="text-sm mt-0.5">
              {(uploadMutation.error as any)?.response?.data?.error?.message || 'Unknown error — check file format and try again.'}
            </div>
          </div>
        </div>
      )}

      {/* Upload history */}
      <div className="card overflow-hidden">
        <div className="px-5 py-4 border-b border-ocean-100 flex items-center justify-between">
          <div className="font-bold text-slate-800">Upload History</div>
          <div className="flex items-center gap-1.5 text-xs text-teal-600 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            Auto-refreshing
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Status</th>
                <th>Rows</th>
                <th>Success %</th>
                <th>Flagged</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {isLoading
                ? [...Array(3)].map((_, i) => (
                    <tr key={i}>
                      {[...Array(7)].map((_, j) => (
                        <td key={j} className="py-3 px-4"><div className="skeleton h-4 rounded w-24" /></td>
                      ))}
                    </tr>
                  ))
                : uploads.length === 0
                  ? <tr><td colSpan={7} className="py-16 text-center text-slate-400">No uploads yet — upload your first ESG file above ☝️</td></tr>
                  : uploads.map((sf: any) => {
                      const s = FILE_STATUS_STYLE[sf.status] || FILE_STATUS_STYLE.pending
                      return (
                        <tr key={sf.id}>
                          <td>
                            <div className="font-semibold text-slate-800 truncate max-w-[220px]">{sf.original_filename}</div>
                            <div className="text-xs text-slate-400 font-mono mt-0.5">{fmtFileSize(sf.file_size_bytes)}</div>
                          </td>
                          <td>
                            <span className="text-sm">
                              {sf.source_type === 'sap_fuel' ? '⛽ SAP' : sf.source_type === 'utility_electricity' ? '⚡ Utility' : '✈️ Travel'}
                            </span>
                          </td>
                          <td>
                            <span className={s.badge}>
                              <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
                              {sf.status}
                            </span>
                          </td>
                          <td className="font-mono font-medium text-slate-700">{sf.total_rows || '—'}</td>
                          <td>
                            <div className="flex items-center gap-2">
                              <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                <div className="h-full bg-teal-400 rounded-full"
                                  style={{ width: `${sf.success_rate || 0}%` }} />
                              </div>
                              <span className={`text-xs font-bold ${(sf.success_rate || 0) >= 90 ? 'text-teal-600' : 'text-amber-600'}`}>
                                {sf.success_rate || 0}%
                              </span>
                            </div>
                          </td>
                          <td>
                            <span className={`font-mono text-sm font-semibold ${sf.flagged_rows > 0 ? 'text-red-600' : 'text-slate-400'}`}>
                              {sf.flagged_rows || 0}
                            </span>
                          </td>
                          <td className="text-xs text-slate-500">
                            {sf.ingestion_timestamp ? format(new Date(sf.ingestion_timestamp), 'MMM d, HH:mm') : '—'}
                          </td>
                        </tr>
                      )
                    })
              }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
