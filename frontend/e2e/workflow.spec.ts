import { test, expect } from '@playwright/test'

test.describe('SmartLegal AI E2E Workflow (SL-048)', () => {
  test('navigates home page and loads key citizen hubs', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/SmartLegal AI/)

    // Verify main CTA heading
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()

    // Navigate to Knowledge Base
    await page.goto('/knowledge-base')
    await expect(page.getByText('Citizen Legal Knowledge Library')).toBeVisible()

    // Navigate to Document Compare page
    await page.goto('/compare')
    await expect(page.getByText('Compare Two Legal Documents')).toBeVisible()

    // Navigate to Jan-Yojana Hub
    await page.goto('/yojana')
    await expect(page.getByText('Jan-Yojana AI Hub')).toBeVisible()
  })

  test('opens demo analysis cockpit without login required', async ({ page }) => {
    await page.goto('/analysis/demo')
    await expect(page.getByText('Residential Rental Agreement')).toBeVisible()
    await expect(page.getByText('Executive Summary')).toBeVisible()
  })
})
