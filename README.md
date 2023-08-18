# french-law-for-llms

> 🚧 Work in progress

Parses [codes.droit.org](https://codes.droit.org)'s XML files into text files that can be _"ingested"_ by an LLM, for example via embeddings.

## Output
Generates:
- 1 contextualized file per law _"article"_.
- 1 folder per _"Code"_

## How to
Requires [Node.js 18+](https://nodejs.org/), [wget](https://formulae.brew.sh/formula/wget) and [ollama](https://ollama.ai/).

```bash
# Install project dependencies
npm install

# Pull latest XML files from codes.droit.org
npm run pull-xml

# Generate LLM-ready txt files
npm run xml-to-txt
```
