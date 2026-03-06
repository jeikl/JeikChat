---
name: "rich-markdown"
description: "Provides rich markdown rendering with code highlighting, emojis, tables, and styled formatting. Use when user wants beautiful markdown output or asks for markdown enhancements."
---

# 🎨 Rich Markdown Renderer

> **📌 Purpose:** Create visually appealing, well-structured markdown responses with proper styling, code highlighting, and formatting

## When to Use

Invoke this skill when:
- User asks for rich markdown formatting
- User wants beautiful/colorful markdown output  
- User asks to enhance markdown display
- User wants to create styled markdown with code blocks, tables, emojis
- Building response templates with markdown

## 📋 Rendering Guidelines

### 1. Basic Markdown Elements

| Element | Syntax | Example |
|---------|--------|---------|
| **Bold** | `**text**` | **Bold Text** |
| *Italic* | `*text*` | *Italic Text* |
| ~~Strikethrough~~ | `~~text~~` | ~~Strikethrough~~ |
| `Code` | `` `code` `` | `Code` |

### 2. Code Blocks

Use triple backticks with language identifier:

```python
def hello():
    print("Hello, World!")
```

```javascript
const greeting = "Hello";
console.log(greeting);
```

### 3. Headers

Use `#` for headers with emoji prefixes:

# 🎯 Header 1
## 🎨 Header 2
### 📝 Header 3

### 4. Lists

**Ordered:**
1. First item
2. Second item
3. Third item

**Unordered:**
- Item one
- Item two
- Item three

**Checkboxes:**
- [x] Completed task
- [ ] Pending task

### 5. Tables

```markdown
| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |
```

### 6. Blockquotes

> This is a blockquote
> Multiple lines supported

### 7. Emojis & Icons

| Icon | Syntax | Display |
|------|--------|---------|
| Check | `:white_check_mark:` | ✅ |
| Cross | `:x:` | ❌ |
| Star | `:star:` | ⭐ |
| Fire | `:fire:` | 🔥 |
| Rocket | `:rocket:` | 🚀 |
| Lightbulb | `:bulb:` | 💡 |
| Book | `:book:` | 📚 |
| Wrench | `:wrench:` | 🔧 |
| Gear | `:gear:` | ⚙️ |

### 8. Colors & Highlights

> **💡 Tip:** Use blockquotes for tips

> **⚠️ Warning:** Important warnings

> **✅ Note:** Additional notes

### 9. Horizontal Rules

---

### 10. Links

[Link Text](https://example.com)

## Response Templates

### Template 1: Feature Description

# 🎯 Feature Name

**Description:** Brief feature description

**Benefits:**
- ✅ Benefit 1
- ✅ Benefit 2
- ✅ Benefit 3

**Usage:**
```python
# Code example here
```

### Template 2: Error Handling

> **❌ Error:** Error description
> 
> **Solution:** How to fix it
> ```python
> # Fix code
> ```

### Template 3: Step-by-Step Guide

# 📋 Step-by-Step Guide

## Step 1: Preparation
- [ ] Prerequisite 1
- [ ] Prerequisite 2

## Step 2: Implementation
```python
# Step 2 code
```

## Step 3: Verification
- Check result 1
- Check result 2

### Template 4: Comparison Table

| Feature | Basic | Pro | Enterprise |
|---------|-------|-----|-----------|
| Feature A | ✅ | ✅ | ✅ |
| Feature B | ❌ | ✅ | ✅ |
| Feature C | ❌ | ❌ | ✅ |

## Styling Conventions

### Header Colors
- `# 🎯` - Main titles (purple/blue)
- `# 🎨` - Section headers (green)
- `# 📝` - Subsection headers (orange)

### List Markers
- Use ✅ for positive items
- Use ❌ for negative items
- Use ⭕ for neutral items

### Code Block Language Tags
```python
# Python
```

```typescript
// TypeScript/JavaScript
```

```bash
# Shell/Bash
```

```json
// JSON
```

## Implementation Notes

- Always use proper markdown syntax
- Include code blocks with language identifiers
- Use tables for structured data
- Add emoji prefixes to headers for visual appeal
- Include practical examples
- Provide clear explanations
