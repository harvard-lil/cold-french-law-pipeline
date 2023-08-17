import fs from 'fs/promises'
import path from 'path'

import 'dotenv/config'

import { parse } from 'node-html-parser'
import { globSync } from 'glob'
import { uuid } from 'uuidv4'

const INPUT_PATH = './xml'

const OUTPUT_PATH = './txt'

const TRANSLATIONS_BACKUP_PATH = './translations_backup'

if ('OLLAMA_API_HOST' in process.env === false) {
  throw new Error('OLLAMA_API_HOST environment variable must be set.')
}

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
  } catch (_err) {
  }

  // For each "article": prepare output, put in context, and write to separate file
  for (const article of dom.querySelectorAll('article[etat="VIGUEUR"]')) {
    const articleTitle = article.getAttribute('modTitle')
    let articleId = article.getAttribute('id')
    const articleNumber = article.getAttribute('num')
    const headings = []
    let output = ''
    let filename = ''

    // Set up an article id if missing
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

    // Intro
    output += `The following is an excerpt of France's "${codeName}" which is part of french law.\n`
    output += 'The rule ("article") described here is currently applicable law. \n\n'

    // Title
    if (articleTitle) {
      output += `Article title: ${articleTitle}:\n`
    }

    if (articleNumber) {
      output += `Article number: ${articleNumber}\n`
    }

    if (articleId && !articleId.startsWith('no-title')) {
      output += `Article identifier: ${articleId}\n`
    }

    // Text
    output += '\nArticle text (french):\n'
    output += `${article.innerText.trim()}\n\n`

    // English translation via ollama
    try {
      const model = 'vicuna:13b'
      const prompt = `Translate the following block of text, which is in french, to english. Your response must only contain the translated text and absolutely nothing else:\n${article.innerText.trim()}`
      const backupPath = path.join(TRANSLATIONS_BACKUP_PATH, `${articleId}.txt`)
      let translation = ''

      // Load translation from text if already available. Otherwise, ask ollama.
      try {
        translation = await fs.readFile(backupPath)
        console.log(`Translation for ${articleId} pulled from disk.`)
      } catch (err) {
        const apiResponse = await fetch(`${process.env.OLLAMA_API_HOST}/api/generate`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ model, prompt })
        })

        const aiResponse = await apiResponse.text()

        for (const jsonLine of aiResponse.split('\n')) {
          try {
            const parsed = JSON.parse(jsonLine)

            if (parsed?.response) {
              translation += parsed.response
            }
          } catch (err) { }
        }
      }

      if (!translation) {
        throw new Error('No translation')
      }

      output += `\nArticle text (translated to english by ${model}):\n`
      output += translation

      await fs.writeFile(backupPath, translation) // Save backup of translation
    } catch (err) {
      console.error(`Could not translate ${articleId}. Skipping.`)
      console.trace(err)
    }

    // Write to file
    filename = path.join(codeOutputPath, `${articleId}.txt`)
    console.log(`Writing ${filename} to disk.`)
    await fs.writeFile(filename, output)
  }
}
