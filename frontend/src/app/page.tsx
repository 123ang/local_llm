"use client";
import Image from "next/image";
import Link from "next/link";
import { BRAND_LOGO_SRC } from "@/components/BrandLogo";
import {
  Brain, Database, FileText, MessageSquare, Shield, Building2,
  Lightbulb, Zap, ArrowRight, ChevronRight, Globe, Lock, BarChart3,
} from "lucide-react";
import { useEffect, useState } from "react";
import { LanguageSwitch } from "@/components/LanguageSwitch";
import { useI18n } from "@/lib/i18n-context";

function AnimatedCounter({ target, suffix = "" }: { target: string; suffix?: string }) {
  return <span>{target}{suffix}</span>;
}

export default function LandingPage() {
  const { t } = useI18n();
  const [scrolled, setScrolled] = useState(false);
  const features = [
    { icon: MessageSquare, title: t("public.feature1Title"), desc: t("public.feature1Copy"), color: "from-red-500 to-orange-500" },
    { icon: Database, title: t("public.feature2Title"), desc: t("public.feature2Copy"), color: "from-emerald-500 to-teal-500" },
    { icon: FileText, title: t("public.feature3Title"), desc: t("public.feature3Copy"), color: "from-blue-500 to-indigo-500" },
    { icon: Lightbulb, title: t("public.feature4Title"), desc: t("public.feature4Copy"), color: "from-purple-500 to-pink-500" },
    { icon: Building2, title: t("public.feature5Title"), desc: t("public.feature5Copy"), color: "from-amber-500 to-orange-500" },
    { icon: Shield, title: t("public.feature6Title"), desc: t("public.feature6Copy"), color: "from-slate-600 to-slate-800" },
  ];
  const stats = [
    { value: "100%", label: t("public.statPrivate") }, { value: "0", label: t("public.statCloud") },
    { value: "∞", label: t("public.statQuestions") }, { value: "<2min", label: t("public.statTime") },
  ];
  const flowSteps = [
    { step: "01", title: t("public.flow1Title"), desc: t("public.flow1Copy"), icon: Database },
    { step: "02", title: t("public.flow2Title"), desc: t("public.flow2Copy"), icon: MessageSquare },
    { step: "03", title: t("public.flow3Title"), desc: t("public.flow3Copy"), icon: Brain },
  ];

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 20);
    window.addEventListener("scroll", handler, { passive: true });
    return () => window.removeEventListener("scroll", handler);
  }, []);

  return (
    <div className="min-h-screen bg-white text-slate-900">
      {/* ─── Navbar ─── */}
      <nav className={`fixed top-0 inset-x-0 z-50 transition-all duration-300 ${scrolled ? "bg-white/90 backdrop-blur-xl shadow-sm border-b border-slate-200/60" : "bg-transparent"}`}>
        <div className="max-w-6xl mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Image
              src={BRAND_LOGO_SRC}
              alt="ANDAI"
              width={140}
              height={47}
              className="h-9 w-auto max-w-[160px] object-contain object-left"
              priority
            />
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
            <a href="#features" className="hover:text-slate-900 transition-colors">{t("public.featuresNav")}</a>
            <a href="#how-it-works" className="hover:text-slate-900 transition-colors">{t("public.howNav")}</a>
            <a href="#architecture" className="hover:text-slate-900 transition-colors">{t("public.architectureNav")}</a>
          </div>
          <div className="flex items-center gap-2"><LanguageSwitch /><Link href="/login" className="px-4 sm:px-5 py-2.5 rounded-xl bg-slate-900 text-white text-sm font-semibold hover:bg-slate-800 transition-colors shadow-lg shadow-slate-900/20">{t("public.signIn")}</Link></div>
        </div>
      </nav>

      {/* ─── Hero ─── */}
      <section className="relative pt-32 pb-20 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-50 via-white to-red-50/40" />
        <div className="absolute top-20 right-0 w-[600px] h-[600px] rounded-full bg-gradient-to-br from-red-100/40 to-orange-100/30 blur-3xl" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] rounded-full bg-gradient-to-tr from-blue-100/30 to-purple-100/20 blur-3xl" />

        <div className="relative max-w-6xl mx-auto px-6">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-red-50 border border-red-200/60 text-red-700 text-xs font-semibold mb-8">
              <Zap size={14} />
              {t("public.badge")}
            </div>

            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-[1.08] tracking-tight">
              <span className="block text-slate-900">{t("public.heroLine1")}</span>
              <span className="block bg-gradient-to-r from-red-600 via-orange-500 to-amber-500 bg-clip-text text-transparent">
                {t("public.heroLine2")}
              </span>
            </h1>

            <p className="mt-6 text-lg sm:text-xl text-slate-600 leading-relaxed max-w-2xl">
              {t("public.heroCopy")}
            </p>

            <div className="mt-10 flex flex-wrap gap-4">
              <Link
                href="/login"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 transition-all shadow-xl shadow-red-600/25 text-sm"
              >
                {t("public.getStarted")} <ArrowRight size={16} />
              </Link>
              <a
                href="#features"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-xl border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 transition-all text-sm"
              >
                {t("public.seeFeatures")} <ChevronRight size={16} />
              </a>
            </div>
          </div>

          {/* Stats row */}
          <div className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-6">
            {stats.map((s) => (
              <div key={s.label} className="text-center p-6 rounded-2xl bg-white border border-slate-200/60 shadow-sm">
                <div className="text-3xl font-extrabold text-slate-900">
                  <AnimatedCounter target={s.value} />
                </div>
                <div className="mt-1 text-xs font-medium text-slate-500 uppercase tracking-wider">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section id="features" className="py-24 bg-slate-50/50">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-red-600 uppercase tracking-wider mb-3">{t("public.featuresLabel")}</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{t("public.featuresTitle")}</h2>
            <p className="mt-4 text-slate-500 max-w-xl mx-auto">{t("public.featuresCopy")}</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f) => (
              <div
                key={f.title}
                className="group relative bg-white rounded-2xl p-7 border border-slate-200/60 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                <div className={`inline-flex items-center justify-center w-11 h-11 rounded-xl bg-gradient-to-br ${f.color} text-white mb-5`}>
                  <f.icon size={20} />
                </div>
                <h3 className="text-lg font-bold mb-2">{f.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section id="how-it-works" className="py-24">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-red-600 uppercase tracking-wider mb-3">{t("public.howLabel")}</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{t("public.howTitle")}</h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {flowSteps.map((s, i) => (
              <div key={s.step} className="relative text-center">
                {i < flowSteps.length - 1 && (
                  <div className="hidden md:block absolute top-12 left-[60%] w-[80%] border-t-2 border-dashed border-slate-300" />
                )}
                <div className="relative inline-flex items-center justify-center w-24 h-24 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-700 text-white mb-6 shadow-xl">
                  <s.icon size={36} />
                  <span className="absolute -top-2 -right-2 w-7 h-7 rounded-full bg-red-600 text-white text-xs font-bold flex items-center justify-center shadow-lg">{s.step}</span>
                </div>
                <h3 className="text-lg font-bold mb-2">{s.title}</h3>
                <p className="text-sm text-slate-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Architecture ─── */}
      <section id="architecture" className="py-24 bg-slate-900 text-white">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">{t("public.architectureLabel")}</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">{t("public.architectureTitle")}</h2>
            <p className="mt-4 text-slate-400 max-w-xl mx-auto">{t("public.architectureCopy")}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { icon: Globe, label: t("public.frontend"), tech: "Next.js 15 · TypeScript · Tailwind CSS 4", desc: t("public.frontendCopy") },
              { icon: Zap, label: t("public.backend"), tech: "FastAPI · Python 3.12 · SQLAlchemy", desc: t("public.backendCopy") },
              { icon: Lock, label: t("public.aiEngine"), tech: "Private local AI runtime", desc: t("public.aiEngineCopy") },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/10 bg-white/5 p-7">
                <div className="inline-flex items-center justify-center w-11 h-11 rounded-xl bg-white/10 text-red-400 mb-5">
                  <item.icon size={20} />
                </div>
                <h3 className="text-lg font-bold mb-1">{item.label}</h3>
                <p className="text-xs text-slate-400 font-mono mb-3">{item.tech}</p>
                <p className="text-sm text-slate-300 leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>

          <div className="mt-12 rounded-2xl border border-white/10 bg-white/5 p-8">
            <div className="flex flex-wrap items-center justify-center gap-6 text-sm font-medium text-slate-400">
              <div className="flex items-center gap-2"><BarChart3 size={16} className="text-emerald-400" /> PostgreSQL 18</div>
              <span className="text-white/20">·</span>
              <div className="flex items-center gap-2"><Database size={16} className="text-blue-400" /> Redis</div>
              <span className="text-white/20">·</span>
              <div className="flex items-center gap-2"><Shield size={16} className="text-amber-400" /> JWT + bcrypt</div>
              <span className="text-white/20">·</span>
              <div className="flex items-center gap-2"><Building2 size={16} className="text-purple-400" /> {t("public.isolation")}</div>
              <span className="text-white/20">·</span>
              <div className="flex items-center gap-2"><FileText size={16} className="text-red-400" /> {t("public.migrations")}</div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="py-24">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight mb-4">{t("public.ctaTitle")}</h2>
          <p className="text-slate-500 mb-10 text-lg">{t("public.ctaCopy")}</p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-red-600 text-white font-semibold hover:bg-red-700 transition-all shadow-xl shadow-red-600/25"
          >
            {t("public.launch")} <ArrowRight size={18} />
          </Link>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-slate-200 py-8">
        <div className="max-w-6xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <Image
              src={BRAND_LOGO_SRC}
              alt="ANDAI"
              width={100}
              height={33}
              className="h-7 w-auto max-w-[120px] object-contain opacity-95"
            />
            <span>· {new Date().getFullYear()}</span>
          </div>
          <p className="text-xs text-slate-400">{t("public.footer")}</p>
        </div>
      </footer>
    </div>
  );
}
