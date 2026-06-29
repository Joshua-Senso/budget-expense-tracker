function SignInPage() {
  return (
    <main className="flex min-h-svh items-center justify-center bg-background px-6 py-16 text-foreground">
      <section className="w-full max-w-md rounded-3xl border bg-card p-8 shadow-sm">
        <p className="text-sm font-medium text-muted-foreground uppercase">
          Private tracker
        </p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">Sign in</h1>
        <p className="mt-3 text-muted-foreground">
          Social sign-in is wired in the auth service; the full sign-in UI lands
          with the next auth feature.
        </p>
      </section>
    </main>
  )
}

export default SignInPage
