---
license: other
language:
- code
- en
task_categories:
- question-answering
- text-generation
- text2text-generation
tags:
- code
viewer: true
pretty_name: StackOverflow Posts Markdown
size_categories:
- 10M&lt;n&lt;100M
---

# StackOverflow Posts Markdown

![StackOverflow Logo](https://stackoverflow.design/assets/img/logos/so/logo-stackoverflow.png)


## Dataset Summary

This dataset contains all posts submitted to StackOverflow before the 14th of June 2023 formatted as **Markdown text**.<br>
The dataset contains ~60 Million posts, totaling ~35GB in size and ~65 billion characters of text.<br>
The data is sourced from [Internet Archive StackExchange Data Dump](https://archive.org/download/stackexchange).

## Dataset Structure

Each record corresponds to one post of a particular type.
Original ordering from the data dump is not exactly preserved due to parallelism in the script used to process the data dump.
The markdown content of each post is contained in the `Body` field. The license for a particular post is contained in the `ContentLicense` field.


### Data Fields
```typescript
{
  Id: long,
  PostTypeId: long, // 1=Question, 2=Answer, 3=Orphaned tag wiki, 4=Tag wiki excerpt, 5=Tag wiki, 6=Moderator nomination, 7=Wiki Placeholder, 8=Privilige Wiki
  AcceptedAnswerId: long | null, // only present if PostTypeId=1
  ParentId: long | null, // only present if PostTypeId=2
  Score: long,
  ViewCount: long | null,
  Body: string | null,
  Title: string | null,
  ContentLicense: string | null,
  FavoriteCount: long | null,
  CreationDate: string | null,
  LastActivityDate: string | null,
  LastEditDate: string | null,
  LastEditorUserId: long | null,
  OwnerUserId: long | null,
  Tags: array<string> | null
}
```
Also consider the [StackExchange Datadump Schema Documentation](https://meta.stackexchange.com/questions/2677/database-schema-documentation-for-the-public-data-dump-and-sede), as all fields
have analogs in the original dump format.

## How to use?

```python
from datasets import load_dataset

# predownload full dataset
ds = load_dataset('mikex86/stackoverflow-posts', split='train')

# dataset streaming (will only download the data as needed)
ds = load_dataset('mikex86/stackoverflow-posts', split='train', streaming=True)

for sample in iter(ds): print(sample["Body"])
```

## How is the text stored?

The original Data Dump formats the "Body" field as HTML, using tags such as `<code>`, `<h1>`, `<ul>`, etc.
This HTML format has been converted to Markdown.

### Markdown format

For reference, [this post on StackOverflow](https://stackoverflow.com/questions/53253940/make-react-useeffect-hook-not-run-on-initial-render) is formatted as follows:

#### Title: Make React useEffect hook not run on initial render

```markdown
According to the docs:

​> `componentDidUpdate()` is invoked immediately after updating occurs. This method is not called for the initial render.

We can use the new `useEffect()` hook to simulate `componentDidUpdate()`, but it seems like `useEffect()` is being ran after every render, even the first time. How do I get it to not run on initial render?

As you can see in the example below, `componentDidUpdateFunction` is printed during the initial render but `componentDidUpdateClass` was not printed during the initial render.

​`​`​`
function ComponentDidUpdateFunction() {
  const [count, setCount] = React.useState(0);
  React.useEffect(() => {
    console.log(""componentDidUpdateFunction"");
  });

  return (
    <div>
      <p>componentDidUpdateFunction: {count} times</p>
      <button
        onClick={() => {
          setCount(count + 1);
        }}
      >
        Click Me
      </button>
    </div>
  );
}
​`​`​`

rest of the post omitted for brevity

```


## Details on the HTML to Markdown conversion

Using Jsoup, the original Body field was converted into a Jsoup Document. The child **nodes** (has special meaning in context of Jsoup) of this document were recursively traversed in a depth-first order.

Jsoup defines `.text()` as follows:
> ... the normalized, combined text of this element and all its children. Whitespace is normalized and trimmed. For example, given HTML <code>&lt;p&gt;Hello &lt;b&gt;there&lt;/b&gt; now! &lt;/p&gt;<code>, p.text() returns "Hello there now!"

Jsoup defines a `Node` as follows:
> The base, abstract Node model. Elements, Documents, Comments etc are all Node instances.

Additionally the existence of the `TextNode` should be noted, which represents floating text inside an HTML document that is not itself an HTML element.
Thus this text tag `<p>Hello<code>World</code></p>` would have two Jsoup child nodes `TextNode(value="Hello")` and `Element(tag="code", value="World")`.
The value `field` of a `TextNode` contains the free standing text without any further treatment (no whitespace stripping, etc.)

### Traversing Rules

- When ecountering a html tag for which a rule exists, children are not further traversed, **unless explicitly stated otherwise**.
- When encountering an `<a>` tag, `[${element.text()}](${element.attr("href")})` is emitted.

- When encountering an `<h1>` tag, `\n# ${element.text()}\n\n` is emitted.
- When encountering an `<h2>` tag, `\n## ${element.text()}\n\n` is emitted.
- When encountering an `<h3>` tag, `\n### ${element.text()}\n\n` is emitted.
- When encountering an `<h4>` tag, `\n#### ${element.text()}\n\n` is emitted.
- When encountering an `<h5>` tag, `\n##### ${element.text()}\n\n` is emitted.
- When encountering an `<h6>` tag, `\n###### ${element.text()}\n\n` is emitted.

- When encountering a `<code>` tag, `` `${element.text()}` ``is emitted
- When encountering a `<pre>` tag and said element **has** a `<code>` child tag, `` ​`​`​`\n${element.text()}`\n​`​`​`\n`` is emitted.
- When encountering a `<pre>` tag and said element **does not** have a `<code>` child tag, **children are traversed further**.
- When encountering an `<li>` tag, `- ` is emitted and **children are traversed further**.
- When encountering a `<blockquote>` tag, `> ` is emitted and **children are traversed further**.
- When encountering an `<hr>` tag, `\n---\n\n` is emitted
- When encountering an `<img>` tag, `![${element.attr("alt")}](${element.attr("src")})` is emitted.
- When encountering a `<table>` tag
  - `\n| ` is emitted
  - For each element of `element.select("th")`
    - `${element.text()} | ` is emitted
  - After the loop `\n| ` is emitted
  - For each element of `element.select("th")`
    - For each character of the `th.text()`
      - `-` is emitted
    - After the loop over each character of th ` | ` is emitted
  - `\n` is emitted
  - For each element of `element.select("tr")` with more than one children of tag type `td`
    - `| ` is emitted
    - For each element of `element.select("td")`
      - `${td.text()} | ` is emitted
    - After the loop over `<td>` elements, `\n` is emitted
  - After the loop over `<tr>` elements, `\n` is emitted
- When encountering a jsoup `TextNode`, `${node.attr(node.nodeName())}` (which is equivalent to accessing the private field `node.value`) is emitted.