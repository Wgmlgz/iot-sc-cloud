import Widget from '../widgets/__WIDGET__.svelte'
import initWidget from '../initWidget'
import 'uno.css'

self.onInit = function () {
  const container = document.createElement('div')
  self.ctx.$container.append(container)
  initWidget(Widget, container, { self: self })
}
