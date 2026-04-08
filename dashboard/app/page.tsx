import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"

const components = [
  "card",
  "checkbox",
  "badge",
  "separator",
  "scroll-area",
  "collapsible",
]

export default function Home() {
  return (
    <main className="min-h-screen bg-muted/40 px-4 py-12 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <Card className="overflow-hidden">
          <CardHeader className="gap-4">
            <div className="flex flex-wrap items-center gap-2">
              <Badge>Next.js</Badge>
              <Badge variant="secondary">shadcn/ui</Badge>
              <Badge variant="outline">Base UI</Badge>
            </div>
            <div className="space-y-2">
              <CardTitle className="text-3xl">Dashboard project is ready</CardTitle>
              <CardDescription>
                `dashboard/` is bootstrapped as an isolated Next.js app with the
                requested shadcn/ui components and extra packages.
              </CardDescription>
            </div>
          </CardHeader>

          <Separator />

          <CardContent className="grid gap-6 py-6 md:grid-cols-[minmax(0,1fr)_320px]">
            <Collapsible
              defaultOpen
              className="rounded-xl border bg-card p-4 shadow-sm"
            >
              <CollapsibleTrigger className="flex w-full items-center justify-between gap-4 rounded-lg text-left text-sm font-medium">
                <span>Installed UI components</span>
                <span className="text-muted-foreground">Toggle</span>
              </CollapsibleTrigger>
              <CollapsibleContent className="pt-4">
                <ScrollArea className="h-52 rounded-lg border bg-background">
                  <div className="space-y-3 p-4">
                    {components.map((component) => (
                      <div
                        key={component}
                        className="flex items-center justify-between rounded-md border bg-muted/40 px-3 py-2"
                      >
                        <span className="font-mono text-sm">{component}</span>
                        <Badge variant="secondary">ready</Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CollapsibleContent>
            </Collapsible>

            <div className="rounded-xl border bg-card p-4 shadow-sm">
              <div className="mb-4 space-y-1">
                <h2 className="font-semibold">Setup checklist</h2>
                <p className="text-muted-foreground text-sm">
                  A minimal verification surface for the installed components.
                </p>
              </div>

              <div className="space-y-4">
                <label className="flex items-start gap-3 rounded-lg border bg-muted/30 p-3">
                  <Checkbox defaultChecked aria-label="Next.js scaffolded" />
                  <span className="space-y-1">
                    <span className="block text-sm font-medium">
                      Next.js project scaffolded
                    </span>
                    <span className="text-muted-foreground block text-sm">
                      App Router, TypeScript, Tailwind CSS, and ESLint are in
                      place.
                    </span>
                  </span>
                </label>

                <label className="flex items-start gap-3 rounded-lg border bg-muted/30 p-3">
                  <Checkbox defaultChecked aria-label="Base UI configured" />
                  <span className="space-y-1">
                    <span className="block text-sm font-medium">
                      Base UI configured
                    </span>
                    <span className="text-muted-foreground block text-sm">
                      shadcn/ui components are wired to Base UI primitives.
                    </span>
                  </span>
                </label>
              </div>
            </div>
          </CardContent>

          <CardFooter className="border-t py-4 text-sm text-muted-foreground">
            Ready for the next implementation step.
          </CardFooter>
        </Card>
      </div>
    </main>
  )
}
