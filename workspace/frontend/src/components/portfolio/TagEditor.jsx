import { useRef, useState } from 'react'
import { Plus, X } from 'lucide-react'
import { Badge, showToast } from '../ui'
import { useAssignTag, useRemoveTag, useTags } from '../../hooks/useTags'
import { getApiErrorMessage } from '../../utils/apiError'

export default function TagEditor({ holdingId, tags = [] }) {
  const [adding, setAdding] = useState(false)
  const [value, setValue] = useState('')
  const inputRef = useRef(null)
  const { data: allTags = [] } = useTags()
  const assignTag = useAssignTag()
  const removeTag = useRemoveTag()

  const startAdding = () => {
    setAdding(true)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    const name = value.trim()
    if (!name) {
      setAdding(false)
      return
    }
    assignTag.mutate(
      { holdingId, name },
      {
        onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not add tag')),
      }
    )
    setValue('')
    setAdding(false)
  }

  const handleRemove = (tagId) => {
    removeTag.mutate(
      { holdingId, tagId },
      {
        onError: (error) => showToast.error(getApiErrorMessage(error, 'Could not remove tag')),
      }
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {tags.map((tag) => (
        <Badge key={tag.tag_id} tone="accent" className="gap-1 pr-1.5">
          {tag.name}
          <button
            type="button"
            onClick={() => handleRemove(tag.tag_id)}
            className="rounded-full p-0.5 hover:bg-accent/20"
            aria-label={`Remove ${tag.name}`}
          >
            <X className="h-2.5 w-2.5" />
          </button>
        </Badge>
      ))}

      {adding ? (
        <form onSubmit={handleSubmit} className="inline-flex">
          <input
            ref={inputRef}
            list="all-tag-names"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onBlur={handleSubmit}
            placeholder="Tag name"
            className="h-6 w-24 rounded border border-border bg-bg px-1.5 text-xs text-text-primary focus:border-accent focus:outline-none"
          />
          <datalist id="all-tag-names">
            {allTags.map((t) => (
              <option key={t.tag_id} value={t.name} />
            ))}
          </datalist>
        </form>
      ) : (
        <button
          type="button"
          onClick={startAdding}
          className="rounded-full border border-dashed border-border p-0.5 text-text-muted hover:border-accent hover:text-accent"
          aria-label="Add tag"
        >
          <Plus className="h-3 w-3" />
        </button>
      )}
    </div>
  )
}
