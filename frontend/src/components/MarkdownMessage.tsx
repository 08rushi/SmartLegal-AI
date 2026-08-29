/**
 * MarkdownMessage — renders an assistant reply as Markdown (GitHub-flavoured, so
 * tables, bold, lists and headings all work) styled for the dark theme.
 *
 * Tables are rendered as real, aligned HTML tables inside a horizontally
 * scrollable wrapper so wide tables stay readable on small screens instead of
 * showing raw "| … |" pipes.
 */
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

const components: Components = {
  table: ({ children }) => (
    <div className="my-2 w-full overflow-x-auto">
      <table className="w-full border-collapse text-left text-[13px] leading-5">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-white/[0.06]">{children}</thead>,
  th: ({ children }) => (
    <th className="border border-white/15 px-3 py-2 font-semibold text-white align-top">{children}</th>
  ),
  td: ({ children }) => (
    <td className="border border-white/10 px-3 py-2 align-top text-slate-200">{children}</td>
  ),
  tr: ({ children }) => <tr className="even:bg-white/[0.02]">{children}</tr>,
  p: ({ children }) => <p className="my-1.5 first:mt-0 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="my-1.5 list-disc space-y-1 pl-5">{children}</ul>,
  ol: ({ children }) => <ol className="my-1.5 list-decimal space-y-1 pl-5">{children}</ol>,
  li: ({ children }) => <li className="pl-0.5">{children}</li>,
  strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
  em: ({ children }) => <em className="italic">{children}</em>,
  h1: ({ children }) => <h3 className="mb-1.5 mt-2 text-sm font-semibold text-white">{children}</h3>,
  h2: ({ children }) => <h3 className="mb-1.5 mt-2 text-sm font-semibold text-white">{children}</h3>,
  h3: ({ children }) => <h4 className="mb-1 mt-2 text-sm font-semibold text-white">{children}</h4>,
  h4: ({ children }) => <h4 className="mb-1 mt-2 text-sm font-semibold text-white">{children}</h4>,
  a: ({ children, href }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" className="text-[#f5c26b] underline underline-offset-2">
      {children}
    </a>
  ),
  code: ({ children }) => (
    <code className="rounded bg-white/10 px-1 py-0.5 text-[12px] text-slate-100">{children}</code>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-2 border-l-2 border-[#f5c26b]/40 pl-3 text-slate-300">{children}</blockquote>
  ),
  hr: () => <hr className="my-3 border-white/10" />,
}

export default function MarkdownMessage({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  )
}
