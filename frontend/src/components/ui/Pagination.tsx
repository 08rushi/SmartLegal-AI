import { Trans, useTranslation } from 'react-i18next'
import { formatLocalNumber } from '../../utils/i18nHelpers'

interface PaginationProps {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}

export function Pagination({ currentPage, totalPages, onPageChange }: PaginationProps) {
  const { t } = useTranslation('shell')
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-between border-t border-slate-800 pt-4 px-2">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage <= 1}
        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-bold text-slate-200 rounded-xl transition-all"
      >
        {t('pagination.previous')}
      </button>

      <span className="text-xs font-semibold text-slate-400">
        <Trans
          t={t}
          i18nKey="pagination.page"
          values={{ current: formatLocalNumber(currentPage), total: formatLocalNumber(totalPages) }}
          components={{ b: <strong className="text-amber-400" /> }}
        />
      </span>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage >= totalPages}
        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed text-xs font-bold text-slate-200 rounded-xl transition-all"
      >
        {t('pagination.next')}
      </button>
    </div>
  )
}
