function DashboardPage() {
  return (
    <section className="flex flex-1 flex-col justify-center gap-3">
      <p className="text-sm font-medium text-muted-foreground uppercase">
        App shell
      </p>
      <h1 className="text-3xl font-semibold tracking-tight">Dashboard</h1>
      <p className="max-w-xl text-muted-foreground">
        Authenticated dashboard routes now have the shared app layout and client
        providers ready for feature modules.
      </p>
    </section>
  )
}

export default DashboardPage
