import fs from "fs/promises"
import path from "path"

import { parse } from 'node-html-parser'
import { globSync } from 'glob'
import { uuid } from 'uuidv4'

const INPUT_PATH = '../xml'

const OUTPUT_PATH = '../txt'

for (const filename of globSync(`${INPUT_PATH}/*.xml`)) {
  const xml = (await fs.readFile(filename)).toString()
  const dom = parse(xml)
  const code = dom.querySelector('code')
  const codeName = code.getAttribute('nom')

  const codeOutputPath = path.join(OUTPUT_PATH, codeName ? codeName : `${uuid()}`)

  // For each code, create a folder 
  await fs.mkdir(codeOutputPath)

  // For each article: prepare output, put in context, and write to separate file
  for (const article of dom.querySelectorAll('article[etat="VIGUEUR"]')) {
    const articleTitle = article.getAttribute('modTitle')
    let articleId = article.getAttribute('cid')
    let headings = []
    let output = ""
    let filename = ""

    // Set up an article id if missing
    if (!articleId || `${articleId}` === "undefined") {
      articleId = `no-title-${uuid()}`
    }

    // Go through parent nodes to pull headings
    if (articleTitle) {
      headings.push(articleTitle)
    }

    let parent = article.parentNode

    while (parent) {
      if (parent.tagName === "T") {
        headings.push(parent.getAttribute("title"))
        parent = parent.parentNode
      } else {
        break
      }
    }

    headings.reverse()

    // Prepare output
    output += `The following is an excerpt of France's "${codeName}" which is part of french law.\n`
    output += `The rule described here is currently applicable law. This text is in French. \n\n`

    output += `Context within "${codeName}":\n`
    for (let i = 0; i < headings.length; i++) {
      const heading = headings[i]
      
      if (heading === articleTitle) {
        continue
      }
      
      output += `${" ".repeat(i+1)}- ${heading.trim()}\n`
    }

    if (articleTitle) {
      output += `\n${articleTitle}:\n\n`
    }

    output += `${article.innerText.trim()}\n`
    
    // Write to file
    filename = path.join(codeOutputPath, `${articleId}.txt`)
    console.log(`Writing ${filename} to disk.`)
    await fs.writeFile(filename, output)
  }

}