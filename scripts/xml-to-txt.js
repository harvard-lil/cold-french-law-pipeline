import fs from 'fs/promises'
import path from 'path'

import { parse } from 'node-html-parser'
import { globSync } from 'glob'
import { uuid } from 'uuidv4'

const INPUT_PATH = './xml'

const OUTPUT_PATH = './txt'

// For each xml file (codes):
for (const filename of globSync(`${INPUT_PATH}/*.xml`)) {
  const xml = (await fs.readFile(filename)).toString()
  const dom = parse(xml)
  const code = dom.querySelector('code')
  const codeName = code.getAttribute('nom')

  const codeOutputPath = path.join(OUTPUT_PATH, codeName || `${uuid()}`)

  // For each "code", create a folder if needed
  try {
    await fs.mkdir(codeOutputPath)
  } catch (_err) { }

  // For each "article": prepare output, put in context, and write to separate file
  for (const article of dom.querySelectorAll('article[etat="VIGUEUR"]')) {
    const articleTitle = article.getAttribute('modTitle')
    let articleId = article.getAttribute('id')
    const articleNumber = article.getAttribute('num')
    const headings = []
    let output = ''
    let filename = ''

    // Create an article id if none provided
    if (!articleId || `${articleId}` === 'undefined') {
      articleId = `no-title-${uuid()}`
    }

    // Go through parent nodes to pull headings (unused at the moment)
    if (articleTitle) {
      headings.push(articleTitle)
    }

    let parent = article.parentNode

    while (parent) {
      if (parent.tagName === 'T') {
        headings.push(parent.getAttribute('title'))
        parent = parent.parentNode
      } else {
        break
      }
    }

    headings.reverse()

    // Title
    if (articleNumber) {
      output += `Article ${articleNumber} du ${codeName}. `
    }

    if (articleTitle) {
      output += `${articleTitle}:\n`
    }

    // Text
    output += `${article.innerText.trim()}`

    // Write to file
    filename = path.join(codeOutputPath, `${articleId}.txt`)
    console.log(`Writing ${filename} to disk.`)
    await fs.writeFile(filename, output)
  }
}
