import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { setProfile, matchYojanaEligibility } from '../store/yojanaSlice'
import { YojanaMatchProfile } from '../types'

interface YojanaDynamicFormProps {
  onMatched?: () => void
}

const INDIAN_STATES = [
  'ALL', 'Maharashtra', 'Madhya Pradesh', 'Uttar Pradesh', 'Delhi',
  'Gujarat', 'Karnataka', 'Tamil Nadu', 'Rajasthan', 'Bihar',
  'West Bengal', 'Punjab', 'Haryana', 'Odisha', 'Telangana', 'Kerala'
]

// Values below are sent to the backend as-is; the visible labels come from the `yojana` namespace.
const OCCUPATIONS = ['farmer', 'student', 'salaried', 'unemployed', 'self_employed', 'construction_worker']

const INCOME_BRACKETS = [150000, 300000, 800000, 1500000]

const CATEGORIES = ['General', 'OBC', 'SC', 'ST', 'Minorities', 'BPL / Ration Card']

export const YojanaDynamicForm: React.FC<YojanaDynamicFormProps> = ({ onMatched }) => {
  const { t } = useTranslation('yojana')
  const dispatch = useAppDispatch()
  const { profile, isLoading } = useAppSelector((s) => s.yojana)

  const [formData, setFormData] = useState<YojanaMatchProfile>(profile)

  // Sync state if external profile changes
  useEffect(() => {
    setFormData(profile)
  }, [profile])

  const handleChange = (field: keyof YojanaMatchProfile, value: any) => {
    setFormData((prev) => {
      const updated = { ...prev, [field]: value }
      
      // Dynamic logic: Reset pregnancy if gender changed to male
      if (field === 'gender' && value === 'male') {
        updated.is_pregnant_or_lactating = false
      }
      // Dynamic logic: Reset landholding if occupation changed away from farmer
      if (field === 'occupation' && value !== 'farmer') {
        updated.land_holding_acres = 0
      }
      return updated
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    dispatch(setProfile(formData))
    dispatch(matchYojanaEligibility(formData))
    if (onMatched) {
      onMatched()
    }
  }

  return (
    <form onSubmit={handleSubmit} className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
      <div className="border-b border-slate-800 pb-4">
        <h3 className="text-xl font-bold text-white flex items-center gap-2">
          <span className="text-indigo-400">✨</span> {t('form.title')}
        </h3>
        <p className="text-xs text-slate-400 mt-1">
          {t('form.intro')}
        </p>
      </div>

      {/* Grid Row 1: State & District */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="yj-state" className="block text-xs font-semibold text-slate-300 mb-1.5">
            {t('form.state')} <span className="text-indigo-400">*</span>
          </label>
          <select id="yj-state"
            value={formData.state}
            onChange={(e) => handleChange('state', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
          >
            {INDIAN_STATES.map((st) => (
              <option key={st} value={st}>
                {st === 'ALL' ? t('form.allIndia') : t(`states.${st}`, { defaultValue: st })}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="yj-district" className="block text-xs font-semibold text-slate-300 mb-1.5">
            {t('form.district')} <span className="text-slate-500">{t('form.optional')}</span>
          </label>
          <input id="yj-district"
            type="text"
            placeholder={t('form.districtPlaceholder')}
            value={formData.district || ''}
            onChange={(e) => handleChange('district', e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>
      </div>

      {/* Grid Row 2: Age & Gender */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="yj-age" className="block text-xs font-semibold text-slate-300 mb-1.5">
            {t('form.age')} <span className="text-indigo-400">*</span>
          </label>
          <input id="yj-age"
            type="number"
            min={1}
            max={100}
            value={formData.age}
            onChange={(e) => handleChange('age', parseInt(e.target.value) || 18)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500 transition-colors"
          />
        </div>

        <div>
          <p id="yj-gender" className="block text-xs font-semibold text-slate-300 mb-1.5">
            {t('form.gender')} <span className="text-indigo-400">*</span>
          </p>
          <div role="group" aria-labelledby="yj-gender" className="flex gap-2">
            {['male', 'female', 'all'].map((g) => (
              <button
                key={g}
                type="button"
                onClick={() => handleChange('gender', g)}
                className={`flex-1 py-2.5 text-xs font-medium rounded-xl border transition-all ${
                  formData.gender === g
                    ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300 shadow-sm'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                }`}
              >
                {t(`form.genders.${g}`)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Row 3: Occupation */}
      <div>
        <p id="yj-occupation" className="block text-xs font-semibold text-slate-300 mb-1.5">
          {t('form.occupation')} <span className="text-indigo-400">*</span>
        </p>
        <div role="group" aria-labelledby="yj-occupation" className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {OCCUPATIONS.map((occ) => (
            <button
              key={occ}
              type="button"
              onClick={() => handleChange('occupation', occ)}
              className={`py-2.5 px-3 text-left text-xs font-medium rounded-xl border transition-all ${
                formData.occupation === occ
                  ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              {t(`form.occupations.${occ}`)}
            </button>
          ))}
        </div>
      </div>

      {/* DYNAMIC CONDITIONAL FIELD 1: Landholding (Only shown if Occupation == 'farmer') */}
      {formData.occupation === 'farmer' && (
        <div className="bg-emerald-950/20 border border-emerald-800/40 rounded-xl p-4 animate-fadeIn">
          <label htmlFor="yj-land" className="block text-xs font-semibold text-emerald-300 mb-1">
            {t('form.land.title')}
          </label>
          <p className="text-[11px] text-emerald-400/80 mb-2">
            {t('form.land.hint')}
          </p>
          <input id="yj-land"
            type="number"
            step="0.1"
            min={0}
            max={100}
            placeholder={t('form.land.placeholder')}
            value={formData.land_holding_acres}
            onChange={(e) => handleChange('land_holding_acres', parseFloat(e.target.value) || 0)}
            className="w-full bg-slate-950 border border-emerald-800/60 rounded-xl px-3.5 py-2 text-sm text-slate-200 focus:outline-none focus:border-emerald-500"
          />
        </div>
      )}

      {/* Row 4: Annual Income Bracket */}
      <div>
        <p id="yj-income" className="block text-xs font-semibold text-slate-300 mb-1.5">
          {t('form.income')} <span className="text-indigo-400">*</span>
        </p>
        <div role="group" aria-labelledby="yj-income" className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          {INCOME_BRACKETS.map((inc) => (
            <button
              key={inc}
              type="button"
              onClick={() => handleChange('annual_income', inc)}
              className={`py-2 px-2.5 text-center text-xs font-medium rounded-xl border transition-all ${
                formData.annual_income === inc
                  ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              {t(`form.incomes.${inc}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Row 5: Social Category & BPL */}
      <div>
        <p id="yj-category" className="block text-xs font-semibold text-slate-300 mb-1.5">
          {t('form.socialCategory')} <span className="text-indigo-400">*</span>
        </p>
        <div role="group" aria-labelledby="yj-category" className="flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => handleChange('category', cat)}
              className={`px-3 py-2 text-xs font-medium rounded-xl border transition-all ${
                formData.category === cat
                  ? 'bg-indigo-600/30 border-indigo-500 text-indigo-300'
                  : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              {t(`form.socialCategories.${cat}`, { defaultValue: cat })}
            </button>
          ))}
        </div>
      </div>

      {/* DYNAMIC CONDITIONAL FIELD 2: Pregnancy Status (Only shown if Gender != 'male') */}
      {formData.gender !== 'male' && (
        <div className="bg-pink-950/20 border border-pink-800/40 rounded-xl p-3.5 flex items-center justify-between animate-fadeIn">
          <div>
            <span className="text-xs font-semibold text-pink-300 block">{t('form.pregnant.title')}</span>
            <span className="text-[11px] text-pink-400/80">{t('form.pregnant.hint')}</span>
          </div>
          <input
            type="checkbox"
            aria-label={t('form.pregnant.title')}
            checked={formData.is_pregnant_or_lactating}
            onChange={(e) => handleChange('is_pregnant_or_lactating', e.target.checked)}
            className="w-5 h-5 accent-pink-500 rounded cursor-pointer"
          />
        </div>
      )}

      {/* Disability Toggle */}
      <div className="bg-slate-950 border border-slate-800 rounded-xl p-3.5 flex items-center justify-between">
        <div>
          <span className="text-xs font-semibold text-slate-300 block">{t('form.disability.title')}</span>
          <span className="text-[11px] text-slate-500">{t('form.disability.hint')}</span>
        </div>
        <input
          type="checkbox"
          aria-label={t('form.disability.title')}
          checked={formData.is_disabled}
          onChange={(e) => handleChange('is_disabled', e.target.checked)}
          className="w-5 h-5 accent-indigo-500 rounded cursor-pointer"
        />
      </div>

      {/* Submit Action */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full py-3.5 px-4 bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-500 hover:to-indigo-400 text-white font-semibold text-sm rounded-xl shadow-lg shadow-indigo-600/20 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            {t('form.submitting')}
          </>
        ) : (
          <>
            <span>{t('form.submit')}</span>
          </>
        )}
      </button>
    </form>
  )
}
