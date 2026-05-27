import Button from "./ui/Button";
import Card from "./ui/Card";
import Badge from "./ui/Badge";
import Input from "./ui/Input";

export const metadata = {
  title: "Components — RepoLens AI",
  description: "UI components showcase",
};

export default function ComponentsPage() {
  return (
    <div className="max-w-5xl mx-auto px-6 py-12 space-y-6">
      <h1 className="text-2xl font-bold">Components</h1>

      <section className="grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="text-lg font-semibold mb-3">Buttons</h3>
          <div className="flex flex-wrap gap-3">
            <Button variant="primary">Primary</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="primary" size="sm">Small</Button>
            <Button variant="primary" size="lg">Large</Button>
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-3">Form Controls</h3>
          <div className="flex flex-col gap-3">
            <Input placeholder="Email" />
            <Input placeholder="Search" />
            <div className="flex items-center gap-2">
              <Button>Submit</Button>
              <Button variant="secondary">Cancel</Button>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-3">Badges</h3>
          <div className="flex flex-wrap gap-2">
            <Badge>Alpha</Badge>
            <Badge className="bg-primary text-primary-foreground">Primary</Badge>
            <Badge className="bg-secondary">Secondary</Badge>
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-3">Layout</h3>
          <p className="text-sm text-muted-foreground">Cards, spacing, and typography match the app theme.</p>
        </Card>
      </section>

      <section>
        <Card>
          <h3 className="text-lg font-semibold mb-3">Playground</h3>
          <p className="text-sm text-muted-foreground mb-4">Try combinations of components to preview look-and-feel.</p>
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <Input placeholder="Type something" />
              <Button>Action</Button>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}
