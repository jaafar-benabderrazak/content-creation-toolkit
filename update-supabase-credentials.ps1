# After you get your NEW Supabase credentials, run this:

# Update backend/.env
Write-Host "Update backend/.env with these values:" -ForegroundColor Yellow
Write-Host ""
Write-Host "SUPABASE_URL=https://YOUR_NEW_PROJECT.supabase.co" -ForegroundColor Cyan
Write-Host "SUPABASE_KEY=your_new_anon_key" -ForegroundColor Cyan
Write-Host "SUPABASE_SERVICE_KEY=your_new_service_role_key" -ForegroundColor Cyan
Write-Host ""

# Update frontend/.env.local
Write-Host "Update frontend/.env.local with these values:" -ForegroundColor Yellow
Write-Host ""
Write-Host "NEXT_PUBLIC_SUPABASE_URL=https://YOUR_NEW_PROJECT.supabase.co" -ForegroundColor Cyan
Write-Host "NEXT_PUBLIC_SUPABASE_ANON_KEY=your_new_anon_key" -ForegroundColor Cyan
Write-Host ""

Write-Host "Then run database_schema_replit.sql in Supabase SQL Editor!" -ForegroundColor Green

