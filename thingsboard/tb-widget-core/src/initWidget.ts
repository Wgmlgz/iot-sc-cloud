import type { SvelteComponent } from 'svelte';

export default function initWidget(Component: new (options: any) => SvelteComponent, targetElement: HTMLElement, props: Record<string, any>): void {
  new Component({
    target: targetElement,
    props
  });
}
