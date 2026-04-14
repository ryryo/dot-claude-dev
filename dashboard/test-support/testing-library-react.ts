// @ts-nocheck
import React, { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';

const HTML_NS = 'http://www.w3.org/1999/xhtml';

class FakeNode {
  nodeType: number;
  nodeName: string;
  ownerDocument: FakeDocument | null;
  parentNode: FakeNode | null;
  childNodes: FakeNode[];
  nodeValue?: string;

  constructor(nodeType: number, nodeName: string, ownerDocument: FakeDocument | null) {
    this.nodeType = nodeType;
    this.nodeName = nodeName;
    this.ownerDocument = ownerDocument;
    this.parentNode = null;
    this.childNodes = [];
  }

  appendChild(child: FakeNode) {
    return this.insertBefore(child, null);
  }

  insertBefore(child: FakeNode, referenceNode: FakeNode | null) {
    if (child.parentNode) {
      child.parentNode.removeChild(child);
    }
    child.parentNode = this;
    if (referenceNode == null) {
      this.childNodes.push(child);
      return child;
    }
    const index = this.childNodes.indexOf(referenceNode);
    if (index === -1) {
      this.childNodes.push(child);
      return child;
    }
    this.childNodes.splice(index, 0, child);
    return child;
  }

  removeChild(child: FakeNode) {
    const index = this.childNodes.indexOf(child);
    if (index !== -1) {
      this.childNodes.splice(index, 1);
      child.parentNode = null;
    }
    return child;
  }

  remove() {
    if (this.parentNode) {
      this.parentNode.removeChild(this);
    }
  }

  contains(node: FakeNode) {
    if (node === this) return true;
    return this.childNodes.some((child) => child.contains(node));
  }

  get firstChild() {
    return this.childNodes[0] ?? null;
  }

  get lastChild() {
    return this.childNodes[this.childNodes.length - 1] ?? null;
  }

  get textContent() {
    if (this.nodeType === 3 || this.nodeType === 8) {
      return this.nodeValue ?? '';
    }
    return this.childNodes.map((child) => child.textContent ?? '').join('');
  }

  set textContent(value: string) {
    this.childNodes = [];
    if (value) {
      const text = this.ownerDocument!.createTextNode(String(value));
      text.parentNode = this;
      this.childNodes.push(text);
    }
  }
}

class FakeElement extends FakeNode {
  tagName: string;
  localName: string;
  namespaceURI: string;
  attributes: Map<string, string>;
  style: Record<string, unknown> & {
    setProperty: (name: string, value: unknown) => void;
    removeProperty: (name: string) => void;
  };
  dataset: Record<string, string>;

  constructor(tagName: string, ownerDocument: FakeDocument, namespaceURI = HTML_NS) {
    super(1, tagName.toUpperCase(), ownerDocument);
    this.tagName = tagName.toUpperCase();
    this.localName = tagName.toLowerCase();
    this.namespaceURI = namespaceURI;
    this.attributes = new Map();
    this.style = {
      setProperty(name: string, value: unknown) {
        this[name] = value;
      },
      removeProperty(name: string) {
        delete this[name];
      },
    };
    this.dataset = {};
  }

  setAttribute(name: string, value: string) {
    this.attributes.set(name, String(value));
  }

  removeAttribute(name: string) {
    this.attributes.delete(name);
  }

  getAttribute(name: string) {
    return this.attributes.get(name) ?? null;
  }

  hasAttribute(name: string) {
    return this.attributes.has(name);
  }

  addEventListener() {}
  removeEventListener() {}

  focus() {
    if (this.ownerDocument) {
      this.ownerDocument.activeElement = this;
    }
  }

  blur() {
    if (this.ownerDocument?.activeElement === this) {
      this.ownerDocument.activeElement = this.ownerDocument.body;
    }
  }
}

class FakeIFrameElement extends FakeElement {
  contentWindow: unknown;

  constructor(ownerDocument: FakeDocument) {
    super('iframe', ownerDocument);
    this.contentWindow = null;
  }
}

class FakeTextNode extends FakeNode {
  constructor(value: string, ownerDocument: FakeDocument) {
    super(3, '#text', ownerDocument);
    this.nodeValue = value;
  }
}

class FakeCommentNode extends FakeNode {
  constructor(value: string, ownerDocument: FakeDocument) {
    super(8, '#comment', ownerDocument);
    this.nodeValue = value;
  }
}

class FakeDocument extends FakeNode {
  documentElement: FakeElement;
  body: FakeElement;
  defaultView: Record<string, unknown> | null;
  activeElement: FakeElement;

  constructor() {
    super(9, '#document', null);
    this.ownerDocument = this;
    this.documentElement = new FakeElement('html', this);
    this.body = new FakeElement('body', this);
    this.documentElement.appendChild(this.body);
    this.defaultView = null;
    this.activeElement = this.body;
  }

  createElement(tagName: string) {
    if (tagName.toLowerCase() === 'iframe') {
      return new FakeIFrameElement(this);
    }
    return new FakeElement(tagName, this);
  }

  createElementNS(namespaceURI: string, tagName: string) {
    return new FakeElement(tagName, this, namespaceURI);
  }

  createTextNode(value: string) {
    return new FakeTextNode(String(value), this);
  }

  createComment(value: string) {
    return new FakeCommentNode(String(value), this);
  }

  addEventListener() {}
  removeEventListener() {}
}

if (typeof document === 'undefined') {
  const fakeDocument = new FakeDocument();
  const fakeWindow = {
    document: fakeDocument,
    navigator: { userAgent: 'node.js' },
    addEventListener() {},
    removeEventListener() {},
    getComputedStyle() {
      return { getPropertyValue() { return ''; } };
    },
    requestAnimationFrame(callback: (timestamp: number) => void) {
      return setTimeout(() => callback(Date.now()), 0);
    },
    cancelAnimationFrame(handle: ReturnType<typeof setTimeout>) {
      clearTimeout(handle);
    },
    setTimeout,
    clearTimeout,
    Node: FakeNode,
    Element: FakeElement,
    HTMLElement: FakeElement,
    HTMLIFrameElement: FakeIFrameElement,
    SVGElement: FakeElement,
    Text: FakeTextNode,
    Comment: FakeCommentNode,
    Document: FakeDocument,
  };

  fakeDocument.defaultView = fakeWindow;

  const globalScope = globalThis as typeof globalThis & Record<string, unknown>;
  globalScope.window = fakeWindow;
  globalScope.document = fakeDocument;
  globalScope.navigator = fakeWindow.navigator;
  globalScope.Node = FakeNode;
  globalScope.Element = FakeElement;
  globalScope.HTMLElement = FakeElement;
  globalScope.HTMLIFrameElement = FakeIFrameElement;
  globalScope.SVGElement = FakeElement;
  globalScope.Text = FakeTextNode;
  globalScope.Comment = FakeCommentNode;
  globalScope.Document = FakeDocument;
  globalScope.requestAnimationFrame = fakeWindow.requestAnimationFrame;
  globalScope.cancelAnimationFrame = fakeWindow.cancelAnimationFrame;
  globalScope.IS_REACT_ACT_ENVIRONMENT = true;
}

export interface RenderHookOptions<Props> {
  initialProps?: Props;
}

export interface RenderHookResult<Result, Props> {
  result: { current: Result };
  rerender: (props?: Props) => void;
  unmount: () => void;
}

const mountedRoots = new Set<{ container: Element; root: Root }>();

export { act };

export function cleanup() {
  for (const entry of mountedRoots) {
    act(() => {
      entry.root.unmount();
    });
    (entry.container as unknown as FakeElement).remove();
  }
  mountedRoots.clear();
}

export function renderHook<Result, Props = void>(
  callback: (props: Props) => Result,
  options: RenderHookOptions<Props> = {},
): RenderHookResult<Result, Props> {
  const container = document.createElement('div');
  document.body.appendChild(container);
  const root = createRoot(container);
  const result = { current: undefined as unknown as Result };
  const entry = { container, root };
  mountedRoots.add(entry);

  function TestComponent(props: { hookProps: Props }) {
    result.current = callback(props.hookProps);
    return null;
  }

  function render(props = options.initialProps as Props) {
    act(() => {
      root.render(React.createElement(TestComponent, { hookProps: props }));
    });
  }

  render();

  return {
    result,
    rerender(nextProps?: Props) {
      render(nextProps as Props);
    },
    unmount() {
      if (!mountedRoots.has(entry)) {
        return;
      }
      act(() => {
        root.unmount();
      });
      mountedRoots.delete(entry);
      (container as unknown as FakeElement).remove();
    },
  };
}

export interface WaitForOptions {
  timeout?: number;
  interval?: number;
}

export async function waitFor<T>(
  assertion: () => T | Promise<T>,
  options: WaitForOptions = {},
): Promise<T> {
  const timeout = options.timeout ?? 1000;
  const interval = options.interval ?? 20;
  const startedAt = Date.now();
  let lastError: unknown;

  while (Date.now() - startedAt <= timeout) {
    try {
      await act(async () => {
        await Promise.resolve();
      });
      return await assertion();
    } catch (error) {
      lastError = error;
      await new Promise((resolve) => {
        setTimeout(resolve, interval);
      });
    }
  }

  throw lastError ?? new Error('waitFor timed out');
}
