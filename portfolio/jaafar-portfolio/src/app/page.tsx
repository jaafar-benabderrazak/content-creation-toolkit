
"use client";
import * as React from "react";
import { motion, useMotionValue, useTransform, animate } from "framer-motion";
import {
  Github, Linkedin, Mail, Globe, Briefcase, GraduationCap, Rocket, FileText, MapPin, Star,
  CheckCircle2, CalendarDays, ArrowRight, ExternalLink, Phone, Search, Moon, Sun, BookOpen,
  ChevronUp, Command, Filter, X,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const PROFILE = {
  name: "Jaafar Benabderrazak",
  tagline: "Machine Learning Engineer · Data Scientist · MLOps · AWS",
  location: "Île-de-France, France",
  about: "Dynamic ML Engineer with 5+ years of experience in data engineering, analytics, predictive modeling, and industrialization. Passionate about AWS, MLOps, and process optimization.",
  links: {
    linkedin: "https://www.linkedin.com/in/jaafar-benabderrazak/",
    github: "https://github.com/jaafar-benabderrazak",
    medium: "https://medium.com/@jaafar-benabderrazak",
    email: "mailto:jaafarbenabderrazak.info@gmail.com",
    phone: "tel:+33659984538",
    cv: "/resume.pdf",
  },
  highlights: [
    "Reduced fare fraud at SNCF from 7.2% to ~5–6%",
    "+15% gas dynamics forecasting accuracy at GRTgaz",
    "AWS Summit 2025: Gen AI Factory showcase",
    "MLOps with ZenML, MLflow, Terraform on AWS",
  ],
  skills: ["Python","SQL","PySpark","TensorFlow","PyTorch","Scikit-Learn","ETL","MLflow","DVC","ZenML","GitLab CI/CD","AWS SageMaker","AWS Glue","AWS Lambda","AWS ECS","AWS S3","Docker","Terraform","Tableau","Power BI","Matplotlib","Seaborn","NLP","Computer Vision"],
  experience: [
    { company: "SNCF", role: "ML Engineer / Data Scientist", period: "Sep 2024 – Dec 2024", bullets: [
      "Reduced fraud rate from 7.2% to 5–6% via experiments & control optimization.",
      "Random Forest, XGBoost, LSTM with exogenous variables for prediction.",
      "Optimized control resources; improved safety & passenger satisfaction.",
    ]},
    { company: "GRTgaz", role: "ML Engineer", period: "Jun 2023 – Aug 2024", bullets: [
      "+15% accuracy on gas dynamics forecasting with productionized models.",
      "Built a Confluence‑integrated chatbot & analytics tooling.",
      "Led a team of 3 engineers to drive efficiency.",
    ]},
    { company: "Devoteam Revolve – LexisNexis", role: "ML Engineer", period: "Sep 2022 – Jun 2023", bullets: [
      "Managed MLOps platform enabling continuous model deployment.",
      "Python refactor + CI/CD cut deploy time by ~40%.",
      "Provisioned AWS infra with Terraform.",
    ]},
    { company: "CGI – Generali", role: "Data Engineer", period: "Jul 2021 – Jul 2022", bullets: [
      "AML fraud detection; ~20% fewer cases.",
      "Scaled PySpark pipelines & automated workflows.",
      "Integrated Neo4j for graph‑based pipelines.",
    ]},
    { company: "CGI – Bpifrance / AG2R La Mondiale", role: "Data Scientist", period: "Mar 2021 – Jun 2021", bullets: [
      "Doc AI for text detection; +25% classification accuracy.",
      "Hyperparameter tuning: +10% performance.",
    ]},
    { company: "CGI – DGFiP", role: "Data Scientist", period: "Apr 2019 – Nov 2020", bullets: [
      "Web scraping + Flask; +35% data collection.",
      "NLP for topic modeling & sentiment analysis.",
    ]},
  ],
  projects: [
    { title: "Fraud Reduction – SNCF TER", period: "2024", tech: ["XGBoost","LSTM","Experimentation"], description: "Predictive modeling + resource optimization to reduce fare fraud from 7.2% to ~5–6%.", link: "#" },
    { title: "Gas Dynamics Forecasting – GRTgaz", period: "2023–2024", tech: ["Python","Forecasting","MLOps"], description: "Production models for gas propagation; +15% accuracy and analytics toolkit.", link: "#" },
    { title: "AML Detection – Generali", period: "2021–2022", tech: ["PySpark","Python","Neo4j"], description: "End‑to‑end AML detection with scalable ETL & graph analytics; ~20% fewer cases.", link: "#" },
  ],
  education: [
    { school: "Centrale Lyon School", period: "2018", detail: "Engineering background (ML/Data)." },
  ],
  certifications: [
    "AWS Cloud Practitioner",
    "AWS Solutions Architect Associate",
    "AWS Machine Learning Specialty",
    "Google TensorFlow Developer",
    "Docker Certified Associate (DCA)",
  ],
  languages: [
    { name: "French", level: "Native" },
    { name: "English", level: "Fluent (TOEFL 103/120, TOEIC 920/990)" },
  ],
};

function useLocalStorage(key: string, initial: any) {
  const [state, setState] = React.useState(() => {
    const v = typeof window !== 'undefined' ? localStorage.getItem(key) : null;
    return v !== null ? JSON.parse(v) : initial;
  });
  React.useEffect(() => { try { localStorage.setItem(key, JSON.stringify(state)); } catch {} }, [key, state]);
  return [state, setState] as const;
}
function useThemeToggle() {
  const [dark, setDark] = useLocalStorage("theme_dark", false);
  React.useEffect(() => { if (dark) document.documentElement.classList.add("dark"); else document.documentElement.classList.remove("dark"); }, [dark]);
  return { dark, setDark };
}
function useActiveSection(ids: string[]) {
  const [active, setActive] = React.useState(ids[0] ?? "");
  React.useEffect(() => {
    const obs = new IntersectionObserver((entries) => { entries.forEach((e) => { if (e.isIntersecting) setActive((e.target as HTMLElement).id); }); }, { rootMargin: "-40% 0px -55% 0px", threshold: 0.01 });
    ids.forEach((id) => { const el = document.getElementById(id); if (el) obs.observe(el); });
    return () => obs.disconnect();
  }, [ids]);
  return active;
}
function ProgressBar() {
  const [progress, setProgress] = React.useState(0);
  React.useEffect(() => {
    const onScroll = () => { const h = document.documentElement; const scrolled = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100; setProgress(scrolled); };
    onScroll(); window.addEventListener("scroll", onScroll, { passive: true }); return () => window.removeEventListener("scroll", onScroll);
  }, []);
  return (<div className="fixed top-0 left-0 right-0 z-[60] h-0.5 bg-transparent"><div className="h-0.5 bg-primary transition-[width]" style={{ width: `${progress}%` }} /></div>);
}
function BackToTop() {
  const [show, setShow] = React.useState(false);
  React.useEffect(() => { const onScroll = () => setShow(window.scrollY > 600); onScroll(); window.addEventListener("scroll", onScroll, { passive: true }); return () => window.removeEventListener("scroll", onScroll); }, []);
  if (!show) return null;
  return (<Button size="icon" className="fixed bottom-5 right-5 rounded-full shadow-lg" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} aria-label="Back to top"><ChevronUp className="h-5 w-5" /></Button>);
}
function AnimatedNumber({ from = 0, to = 0, duration = 1.2 }: { from?: number, to?: number, duration?: number }) {
  const mv = useMotionValue(from); const rounded = useTransform(mv, (v) => Math.round(v).toLocaleString());
  React.useEffect(() => { const controls = animate(mv, to, { duration, ease: "easeOut" }); return () => controls.stop(); }, [to, duration, mv]);
  return <motion.span>{rounded}</motion.span>;
}
const Section = ({ id, icon: Icon, title, subtitle, children }: any) => (
  <section id={id} className="scroll-mt-28">
    <div className="flex items-center gap-3 mb-3"><div className="p-2 rounded-2xl bg-muted/70 backdrop-blur shadow-sm"><Icon className="h-5 w-5" /></div>
      <div><h2 className="text-xl font-semibold leading-tight">{title}</h2>{subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}</div></div>{children}
  </section>
);
const LinkIcon = ({ href, children }: any) => (<a href={href} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 underline decoration-dotted hover:decoration-solid">{children} <ExternalLink className="h-3.5 w-3.5" /></a>);
function SkillFilter({ skills }: { skills: string[] }) {
  const [query, setQuery] = React.useState(""); const filtered = React.useMemo(() => skills.filter(s => s.toLowerCase().includes(query.toLowerCase())), [skills, query]);
  return (<div><div className="flex items-center gap-2 mb-4"><div className="relative w-full md:w-96"><input className="w-full rounded-xl border px-3 py-2 pr-9 text-sm focus:outline-none focus:ring" placeholder="Filter skills (e.g., AWS, PySpark, MLflow)" value={query} onChange={(e) => setQuery(e.target.value)} /><Search className="h-4 w-4 absolute right-3 top-2.5 text-slate-400" /></div></div><div className="flex flex-wrap gap-2">{filtered.map((s) => (<Badge key={s} className="rounded-xl" variant="secondary">{s}</Badge>))}{filtered.length === 0 && <span className="text-xs text-muted-foreground">No skills match your search.</span>}</div></div>);
}
function TimelineItem({ role, company, period, bullets }: { role: string, company: string, period: string, bullets: string[] }) {
  const [open, setOpen] = React.useState(true);
  return (<div className="relative pl-6"><div className="absolute left-0 top-1.5 h-3 w-3 rounded-full bg-primary" />
    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2"><h3 className="font-semibold cursor-pointer" onClick={() => setOpen(!open)}>{role} · <span className="text-muted-foreground">{company}</span></h3><p className="text-xs text-muted-foreground flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" />{period}</p></div>
    {open && (<ul className="mt-2 grid gap-2 text-sm list-disc list-inside">{bullets.map((b) => (<li key={b}>{b}</li>))}</ul>)}</div>);
}
function ProjectFilters({ projects, onFilter }: { projects: any[], onFilter: (f:any)=>void }) {
  const allTags = React.useMemo(() => { const set = new Set<string>(); projects.forEach(p => p.tech.forEach((t:string) => set.add(t))); return Array.from(set).sort(); }, [projects]);
  const [search, setSearch] = React.useState(""); const [active, setActive] = React.useState<string[]>([]);
  React.useEffect(() => { onFilter({ search, tags: active }); }, [search, active, onFilter]);
  const toggle = (tag: string) => setActive((prev) => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]); const clear = () => { setActive([]); setSearch(""); };
  return (<div className="mb-4"><div className="flex items-center gap-2 mb-3"><div className="relative w-full md:w-96"><input className="w-full rounded-xl border px-3 py-2 pr-9 text-sm focus:outline-none focus:ring" placeholder="Search projects (title, description)" value={search} onChange={(e) => setSearch(e.target.value)} /><Search className="h-4 w-4 absolute right-3 top-2.5 text-slate-400" /></div><Badge variant="secondary" className="rounded-xl flex items-center gap-1"><Filter className="h-3.5 w-3.5" />Filters</Badge>{(active.length || search) ? (<Button size="sm" variant="ghost" onClick={clear} className="rounded-xl"><X className="h-4 w-4 mr-1" />Clear</Button>) : null}</div><div className="flex flex-wrap gap-2">{allTags.map(tag => (<button key={tag} onClick={() => toggle(tag)} className={`text-xs px-2.5 py-1 rounded-xl border ${active.includes(tag) ? 'bg-primary text-white border-primary' : 'hover:bg-muted'}`}>{tag}</button>))}</div></div>);
}
function ProjectCard({ title, period, description, tech, link }: any) {
  return (<motion.div initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}><Card className="shadow-sm hover:shadow-md hover:-translate-y-0.5 transition will-change-transform"><CardContent className="p-5"><div className="flex items-center justify-between gap-2"><div><h3 className="font-semibold">{title}</h3><p className="text-xs text-muted-foreground">{period}</p></div>{link && link !== "#" && (<a href={link} className="text-sm underline decoration-dotted" target="_blank" rel="noreferrer">Demo</a>)}</div><p className="mt-3 text-sm text-muted-foreground">{description}</p><div className="mt-3 flex flex-wrap gap-2">{tech.map((t: string) => (<Badge key={t} variant="outline" className="rounded-xl">{t}</Badge>))}</div></CardContent></Card></motion.div>);
}
function CommandPalette({ open, setOpen, sections }: any) {
  const [query, setQuery] = React.useState("");
  React.useEffect(() => {
    const onKey = (e: KeyboardEvent) => { const mac = /(Mac|iPhone|iPod|iPad)/i.test(navigator.platform);
      if ((mac && (e as any).metaKey && e.key.toLowerCase() === 'k') || (!mac && (e as any).ctrlKey && e.key.toLowerCase() === 'k')) { e.preventDefault(); setOpen(true); } };
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey);
  }, [setOpen]);
  const items = React.useMemo(() => ([{ id: 'home', label: 'Go to top', href: '#main' }, ...sections.map((s: string) => ({ id: s, label: s.charAt(0).toUpperCase()+s.slice(1), href: `#${s}` }))]).filter((i: any) => i.label.toLowerCase().includes(query.toLowerCase())), [query, sections]);
  if (!open) return null;
  return (<div className="fixed inset-0 z-[70] bg-black/40 backdrop-blur-sm" onClick={() => setOpen(false)}><div className="max-w-lg mx-auto mt-24" onClick={(e) => e.stopPropagation()}><div className="rounded-2xl border bg-background shadow-xl overflow-hidden"><div className="flex items-center gap-2 px-3 py-2 border-b"><Command className="h-4 w-4 text-muted-foreground" /><input autoFocus value={query} onChange={(e)=>setQuery(e.target.value)} placeholder="Type to jump to a section… (Cmd+K / Ctrl+K)" className="w-full bg-transparent outline-none text-sm py-1" /></div><ul className="max-h-64 overflow-auto">{items.map((it: any) => (<li key={it.id}><a href={it.href} onClick={()=>setOpen(false)} className="block px-4 py-2 text-sm hover:bg-muted">{it.label}</a></li>))}{items.length===0 && <li className="px-4 py-3 text-xs text-muted-foreground">No results</li>}</ul></div></div></div>);
}

export default function Portfolio() {
  const { dark, setDark } = useThemeToggle();
  const sections = React.useMemo(() => ["experience", "projects", "skills", "education", "certifications", "languages", "contact"], []);
  const active = useActiveSection(sections);
  const [cmdOpen, setCmdOpen] = React.useState(false);

  const [filters, setFilters] = React.useState({ search: "", tags: [] as string[] });
  const filteredProjects = React.useMemo(() => {
    return PROFILE.projects.filter(p => {
      const q = filters.search.toLowerCase();
      const inText = (p.title + " " + p.description).toLowerCase().includes(q);
      const tagOk = filters.tags.length === 0 || filters.tags.every(t => p.tech.includes(t));
      return inText && tagOk;
    });
  }, [filters]);

  const years = new Date().getFullYear() - 2019;
  const shipped = 18;
  const talks = 6;

  return (
    <div className="min-h-screen scroll-smooth relative bg-gradient-to-b from-white to-slate-50 dark:from-slate-950 dark:to-slate-900 text-slate-900 dark:text-slate-100">
      <div aria-hidden className="pointer-events-none select-none absolute -top-32 -right-32 h-64 w-64 rounded-full bg-primary/10 blur-3xl" />
      <div aria-hidden className="pointer-events-none select-none absolute top-1/3 -left-40 h-72 w-72 rounded-full bg-emerald-400/10 dark:bg-emerald-300/10 blur-3xl" />

      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:bg-white focus:text-slate-900 dark:focus:bg-slate-900 dark:focus:text-white focus:px-3 focus:py-2 focus:rounded-xl">Skip to content</a>

      <ProgressBar />

      <header className="sticky top-0 z-50 backdrop-blur bg-white/70 dark:bg-slate-900/70 border-b">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-2xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 grid place-items-center font-bold ring-2 ring-primary/40">JB</div>
            <div><p className="text-sm font-semibold">{PROFILE.name}</p><p className="text-xs text-muted-foreground">{PROFILE.tagline}</p></div>
          </div>
          <nav className="hidden md:flex items-center gap-1">
            {sections.map((id) => (
              <a key={id} href={`#${id}`} className={`text-xs px-3 py-1.5 rounded-xl transition hover:bg-muted ${active === id ? "bg-muted font-medium" : ""}`}>
                {id.charAt(0).toUpperCase() + id.slice(1)}
              </a>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <Button size="icon" variant="ghost" className="rounded-xl" onClick={() => setCmdOpen(true)} aria-label="Open command palette"><Command className="h-5 w-5" /></Button>
            <Button size="icon" variant="ghost" className="rounded-xl" onClick={() => setDark((v: boolean) => !v)} aria-label="Toggle theme">{dark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}</Button>
            <a href={PROFILE.links.linkedin} target="_blank" rel="noreferrer" className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"><Linkedin className="h-5 w-5" /></a>
            <a href={PROFILE.links.github} target="_blank" rel="noreferrer" className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"><Github className="h-5 w-5" /></a>
            <a href={PROFILE.links.email} className="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800"><Mail className="h-5 w-5" /></a>
          </div>
        </div>
      </header>

      <main id="main" className="max-w-6xl mx-auto px-4 pb-24">
        <section className="py-12 md:py-16">
          <div className="grid md:grid-cols-3 gap-6 items-stretch">
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="md:col-span-2">
              <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight mb-3">
                Hey, I’m {PROFILE.name} <span className="text-slate-500 dark:text-slate-400">👋</span>
              </h1>
              <p className="text-lg text-slate-700 dark:text-slate-300 mb-4">{PROFILE.tagline}</p>
              <div className="flex flex-wrap gap-2 mb-6">
                <Badge className="rounded-xl" variant="secondary"><MapPin className="h-3.5 w-3.5 mr-1" />{PROFILE.location}</Badge>
                {PROFILE.highlights.map((t) => (<Badge key={t} className="rounded-xl" variant="outline">{t}</Badge>))}
              </div>
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed mb-6">{PROFILE.about}</p>
              <div className="grid grid-cols-3 gap-3 mb-6">
                <Card className="shadow-sm"><CardContent className="p-4 text-center"><p className="text-xs text-muted-foreground">Years of impact</p><p className="text-2xl font-bold"><AnimatedNumber to={years} /></p></CardContent></Card>
                <Card className="shadow-sm"><CardContent className="p-4 text-center"><p className="text-xs text-muted-foreground">ML projects shipped</p><p className="text-2xl font-bold"><AnimatedNumber to={shipped} /></p></CardContent></Card>
                <Card className="shadow-sm"><CardContent className="p-4 text-center"><p className="text-xs text-muted-foreground">Talks / demos</p><p className="text-2xl font-bold"><AnimatedNumber to={talks} /></p></CardContent></Card>
              </div>
              <div className="flex flex-wrap gap-3">
                <Button asChild className="rounded-2xl"><a href="#projects"><Rocket className="mr-2 h-4 w-4" />See projects</a></Button>
                <Button asChild variant="outline" className="rounded-2xl"><a href={PROFILE.links.cv}><FileText className="mr-2 h-4 w-4" />Download CV</a></Button>
                <Button asChild variant="ghost" className="rounded-2xl"><a href={PROFILE.links.medium}><BookOpen className="mr-2 h-4 w-4" />Writing</a></Button>
              </div>
            </motion.div>

            <Card className="md:col-span-1 shadow-sm">
              <CardContent className="p-5">
                <div className="flex items-center gap-2 mb-3"><Star className="h-4 w-4" /><p className="font-semibold">Highlights</p></div>
                <ul className="space-y-3 text-sm">{PROFILE.highlights.map((h) => (<li key={h} className="flex gap-2 items-start"><CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" /><span>{h}</span></li>))}</ul>
                <div className="mt-5 pt-4 border-t text-xs text-muted-foreground"><p>Open to ML/MLOps opportunities & collaborations.</p></div>
              </CardContent>
            </Card>
          </div>
        </section>

        <Section id="experience" icon={Briefcase} title="Experience" subtitle="Impact-focused timeline (click a role to collapse/expand)">
          <div className="relative pl-4 border-l">
            {PROFILE.experience.map((exp) => (
              <Card key={exp.company} className="shadow-sm mb-4"><CardContent className="p-5"><TimelineItem role={exp.role} company={exp.company} period={exp.period} bullets={exp.bullets} /></CardContent></Card>
            ))}
          </div>
        </Section>

        <Section id="projects" icon={Rocket} title="Selected Projects">
          <ProjectFilters projects={PROFILE.projects} onFilter={setFilters} />
          <div className="grid md:grid-cols-2 gap-4">
            {filteredProjects.map((p) => (<ProjectCard key={p.title} {...p} />))}
            {filteredProjects.length === 0 && (<Card className="shadow-sm"><CardContent className="p-6 text-sm text-muted-foreground">No projects match your filters.</CardContent></Card>)}
          </div>
        </Section>

        <Section id="skills" icon={Star} title="Skills & Tools">
          <Card className="shadow-sm"><CardContent className="p-5"><SkillFilter skills={PROFILE.skills} /></CardContent></Card>
        </Section>

        <Section id="education" icon={GraduationCap} title="Education">
          <div className="grid gap-4">
            {PROFILE.education.map((e) => (
              <Card key={e.school} className="shadow-sm"><CardContent className="p-5"><div className="flex items-center justify-between">
                <div><h3 className="font-semibold">{e.school}</h3><p className="text-sm text-muted-foreground">{e.detail}</p></div>
                <span className="text-xs text-muted-foreground">{e.period}</span>
              </div></CardContent></Card>
            ))}
          </div>
        </Section>

        <Section id="certifications" icon={CheckCircle2} title="Certifications">
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
            {PROFILE.certifications.map((c) => (
              <Card key={c} className="shadow-sm"><CardContent className="p-4 text-sm flex items-center justify-between"><span>{c}</span><Badge variant="secondary" className="rounded-xl">Verified</Badge></CardContent></Card>
            ))}
          </div>
        </Section>

        <Section id="languages" icon={Globe} title="Languages">
          <Card className="shadow-sm"><CardContent className="p-5 flex flex-wrap gap-3 text-sm">{PROFILE.languages.map((l) => (<Badge key={l.name} variant="outline" className="rounded-xl">{l.name} — {l.level}</Badge>))}</CardContent></Card>
        </Section>

        <Section id="contact" icon={Mail} title="Contact">
          <Card className="shadow-sm"><CardContent className="p-5">
            <div className="grid md:grid-cols-2 gap-6 items-start">
              <div>
                <p className="text-sm text-slate-700 dark:text-slate-300 mb-3">For opportunities, collaborations, or just to say hello, feel free to reach out.</p>
                <div className="flex flex-wrap gap-3">
                  <Button asChild className="rounded-2xl"><a href={PROFILE.links.email}><Mail className="mr-2 h-4 w-4" />Email</a></Button>
                  <Button asChild variant="outline" className="rounded-2xl"><a href={PROFILE.links.phone}><Phone className="mr-2 h-4 w-4" />Call</a></Button>
                  <Button asChild variant="ghost" className="rounded-2xl"><a href={PROFILE.links.linkedin}><Linkedin className="mr-2 h-4 w-4" />LinkedIn</a></Button>
                  <Button asChild variant="ghost" className="rounded-2xl"><a href={PROFILE.links.github}><Github className="mr-2 h-4 w-4" />GitHub</a></Button>
                  <Button asChild variant="ghost" className="rounded-2xl"><a href={PROFILE.links.medium}><BookOpen className="mr-2 h-4 w-4" />Medium</a></Button>
                </div>
                <div className="mt-4 flex flex-wrap gap-3"><Button asChild className="rounded-2xl"><a href={PROFILE.links.cv}><FileText className="mr-2 h-4 w-4" />Download Résumé (PDF)</a></Button></div>
              </div>
              <div className="text-sm text-muted-foreground space-y-2">
                <p>Prefer a quick overview? Check my <LinkIcon href={PROFILE.links.cv}>one‑page résumé</LinkIcon>, <LinkIcon href={PROFILE.links.linkedin}>LinkedIn</LinkIcon>, and <LinkIcon href={PROFILE.links.medium}>recent writing</LinkIcon>.</p>
                <p className="flex items-center gap-2 text-muted-foreground"><Globe className="h-4 w-4" /> Available in EU time zones; based in {PROFILE.location}.</p>
              </div>
            </div>
          </CardContent></Card>
        </Section>
      </main>

      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        <div className="max-w-6xl mx-auto px-4">
          © {new Date().getFullYear()} {PROFILE.name}. Built with Next.js, Tailwind & Framer Motion. <ArrowRight className="inline h-3.5 w-3.5" />
        </div>
      </footer>

      <BackToTop />
      <CommandPalette open={cmdOpen} setOpen={setCmdOpen} sections={sections} />
    </div>
  );
}
