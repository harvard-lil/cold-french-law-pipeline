# french-law-to-txt
Parses [codes.droit.org](https://codes.droit.org)'s XML files into text files that can be _"ingested"_ by an LLM, for example via embeddings.

## Output
Generates:
- 1 contextualized file per law _"article"_.
- 1 folder per _"Code"_

## How to
Requires [Node.js 18+](https://nodejs.org/).

```bash
# Install project dependencies
npm install

# Pull latest XML files from codes.droit.org
npm run pull-xml

# Generate LLM-ready txt files
npm run xml-to-txt
```

## About the "index" folder
This folder contains information manually extracted from Wikipedia France about _most_ of the available _"codes"_. 

Its purpose is to give context, and help make associations between questions / themes and specific codes. 