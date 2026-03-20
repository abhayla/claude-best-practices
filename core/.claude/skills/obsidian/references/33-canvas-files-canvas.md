# 3.3 Canvas Files (.canvas)

### 3.3 Canvas Files (.canvas)

Canvas files use the [JSON Canvas Spec 1.0](https://jsoncanvas.org/):

```json
{
  "nodes": [
    {
      "id": "a1b2c3d4e5f67890",
      "type": "text",
      "x": 0,
      "y": 0,
      "width": 400,
      "height": 200,
      "text": "# Node Title\n\nMarkdown content here"
    },
    {
      "id": "b2c3d4e5f6789012",
      "type": "file",
      "x": 500,
      "y": 0,
      "width": 400,
      "height": 200,
      "file": "path/to/note.md"
    },
    {
      "id": "c3d4e5f678901234",
      "type": "link",
      "x": 0,
      "y": 300,
      "width": 400,
      "height": 200,
      "url": "https://example.com"
    },
    {
      "id": "d4e5f67890123456",
      "type": "group",
      "x": -50,
      "y": -50,
      "width": 1000,
      "height": 600,
      "label": "Group Label"
    }
  ],
  "edges": [
    {
      "id": "e5f6789012345678",
      "fromNode": "a1b2c3d4e5f67890",
      "toNode": "b2c3d4e5f6789012",
      "fromSide": "right",
      "toSide": "left",
      "label": "relates to"
    }
  ]
}
```

**Canvas rules:**
- Node IDs: 16-character hexadecimal strings (unique)
- Every node requires: `id`, `type`, `x`, `y`, `width`, `height`
- Text nodes: `text` field with Markdown content
- File nodes: `file` field with vault-relative path
- Link nodes: `url` field
- Group nodes: optional `label`, optional `background` (CSS color)
- Edge sides: `top`, `right`, `bottom`, `left`
- Edges can have: `color` (CSS), `label` (text)

