import { useDispatch, useSelector } from 'react-redux'
import type { RootState, AppDispatch } from '../store'

// Use these typed hooks everywhere instead of plain useDispatch/useSelector
export const useAppDispatch = () => useDispatch<AppDispatch>()
export const useAppSelector = <T>(selector: (state: RootState) => T): T =>
  useSelector(selector)
