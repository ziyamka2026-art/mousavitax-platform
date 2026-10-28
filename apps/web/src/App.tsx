```tsx
import { useState } from "react";

import Ask from "./pages/Ask";
import Terms from "./pages/Terms";
import ConsultationThread from "./pages/ConsultationThread";
import Placeholder from "./pages/Placeholder";

import { menu, type Role, homePath } from "./config/roles";

const labels: Record<string, string> = {
  dashboard: "داشبورد",
  office: "دفتر مشاوره",
  ask: "پرسش مالیاتی",
  documents: "اسناد",
  consultations: "مشاوره‌ها",
  terms: "شرایط استفاده",
};

function getHomePage(role: Role): string {
  return homePath[role].replace(/^\/+/, "");
}

function getDraftAction(): string | undefined {
  if (typeof window === "undefined") {
    return undefined;
  }

  return (
    new URLSearchParams(window.location.search).get("draftAction") ||
    undefined
  );
}

export default function App() {
  const [role, setRole] = useState<Role>("owner");
  const [page, setPage] = useState<string>(() => getHomePage("owner"));

  const items = menu[role];

  const changeRole = (nextRole: Role) => {
    setRole(nextRole);
    setPage(getHomePage(nextRole));
  };

  const content =
    page === "ask" ? (
      <Ask />
    ) : page === "terms" ? (
      <Terms />
    ) : page === "consultations" ? (
      <ConsultationThread draftAction={getDraftAction()} />
    ) : (
      <Placeholder title={labels[page] || "پنل"} />
    );

  return (
    <div className="shell" dir="rtl">
      <aside>
        <h2>MKA / MousaviTax</h2>

        <label htmlFor="current-role">نقش فعلی</label>

        <select
          id="current-role"
          value={role}
          onChange={(event) => changeRole(event.target.value as Role)}
        >
          {Object.keys(menu).map((roleName) => (
            <option key={roleName} value={roleName}>
              {roleName}
            </option>
          ))}
        </select>

        <nav aria-label="منوی اصلی">
          {items.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => setPage(item)}
              aria-current={page === item ? "page" : undefined}
            >
              {labels[item] || item}
            </button>
          ))}
        </nav>

        <small>
          این انتخاب نقش صرفاً رابط کاربری است؛ مجوز واقعی باید در Backend
          اعمال و اعتبارسنجی شود.
        </small>
      </aside>

      <main>{content}</main>
    </div>
  );
}
```
