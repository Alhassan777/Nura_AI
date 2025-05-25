import { Client } from '@notionhq/client';

class NotionService {
  private notion: Client;
  private databaseId: string;
  
  constructor(notionApiKey: string, databaseId: string) {
    this.notion = new Client({ auth: notionApiKey });
    this.databaseId = databaseId;
  }
  
  /**
   * Create a new page in the Notion database with reflection session data
   */
  async createReflectionPage(title: string, summary: string, imageUrl?: string): Promise<string> {
    try {
      const response = await this.notion.pages.create({
        parent: {
          database_id: this.databaseId,
        },
        properties: {
          title: {
            title: [
              {
                text: {
                  content: title,
                },
              },
            ],
          },
          Date: {
            date: {
              start: new Date().toISOString(),
            },
          },
        },
        children: this.buildPageContent(summary, imageUrl),
      });
      
      // The response.id contains the page ID, which we can use to construct the URL
      const pageId = response.id.replace(/-/g, '');
      return `https://notion.so/${pageId}`;
    } catch (error) {
      console.error('Error creating Notion page:', error);
      throw error;
    }
  }
  
  /**
   * Build page content for Notion
   */
  private buildPageContent(summary: string, imageUrl?: string): any[] {
    const blocks: any[] = [
      {
        object: 'block',
        type: 'heading_1',
        heading_1: {
          rich_text: [
            {
              type: 'text',
              text: {
                content: 'Reflection Session Summary',
              },
            },
          ],
        },
      },
    ];
    
    // Add summary as markdown blocks
    const paragraphs = summary.split('\n\n');
    for (const paragraph of paragraphs) {
      if (paragraph.startsWith('# ')) {
        // Handle heading
        blocks.push({
          object: 'block',
          type: 'heading_2',
          heading_2: {
            rich_text: [
              {
                type: 'text',
                text: {
                  content: paragraph.substring(2),
                },
              },
            ],
          },
        });
      } else if (paragraph.startsWith('- ')) {
        // Handle list item
        blocks.push({
          object: 'block',
          type: 'bulleted_list_item',
          bulleted_list_item: {
            rich_text: [
              {
                type: 'text',
                text: {
                  content: paragraph.substring(2),
                },
              },
            ],
          },
        });
      } else {
        // Regular paragraph
        blocks.push({
          object: 'block',
          type: 'paragraph',
          paragraph: {
            rich_text: [
              {
                type: 'text',
                text: {
                  content: paragraph,
                },
              },
            ],
          },
        });
      }
    }
    
    // Add image if provided
    if (imageUrl) {
      blocks.push({
        object: 'block',
        type: 'heading_2',
        heading_2: {
          rich_text: [
            {
              type: 'text',
              text: {
                content: 'Emotional Visualization',
              },
            },
          ],
        },
      });
      
      blocks.push({
        object: 'block',
        type: 'image',
        image: {
          type: 'external',
          external: {
            url: imageUrl,
          },
        },
      });
    }
    
    return blocks;
  }
}

export default NotionService; 