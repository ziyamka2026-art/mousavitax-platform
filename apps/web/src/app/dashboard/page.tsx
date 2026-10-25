import { createClient } from "@/lib/supabase/server"
import { redirect } from "next/navigation"

export default async function DashboardPage() {
  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect("/login")
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-4">داشبورد موصوی‌تکس</h1>
        <p className="text-slate-400 mb-6">
          خوش آمدید {user.user_metadata?.full_name || user.email}
        </p>

        <div className="rounded-lg border border-slate-800 bg-[#121a2c] p-6">
          <p>صفحه داشبورد با موفقیت ساخته شد.</p>
          <p className="text-sm text-slate-500 mt-2">در مراحل بعدی بخش‌های مدیریت شرکت، فاکتور و اظهارنامه اضافه خواهد شد.</p>
        </div>
      </div>
    </div>
  )
}
