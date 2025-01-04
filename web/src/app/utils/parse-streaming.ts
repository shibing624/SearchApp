import { Relate } from "@/app/interfaces/relate";
import { Source } from "@/app/interfaces/source";

const LLM_SPLIT = "__LLM_RESPONSE__";
const RELATED_SPLIT = "__RELATED_QUESTIONS__";

// Get the base URL for API calls
const getApiUrl = () => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || '';
  return `${baseUrl}/query`;
};

export const parseStreaming = async (
  controller: AbortController,
  query: string,
  search_uuid: string,
  onSources: (value: Source[]) => void,
  onMarkdown: (value: string) => void,
  onRelates: (value: Relate[]) => void,
  onError?: (status: number) => void,
) => {
  const decoder = new TextDecoder();
  let buffer = "";
  let sourcesProcessed = false;

  try {
    const response = await fetch(getApiUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        search_uuid,
        generate_related_questions: true,
      }),
      signal: controller.signal,
    });

    if (!response.ok) {
      onError?.(response.status);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("No reader available");
    }

    while (true) {
      const { done, value } = await reader.read();
      
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;

      // Process sources first if not already processed
      if (buffer.includes(LLM_SPLIT) && !sourcesProcessed) {
        const [sourcesStr, rest] = buffer.split(LLM_SPLIT);
        try {
          const sourcesData = JSON.parse(sourcesStr);
          if (Array.isArray(sourcesData)) {
            onSources(sourcesData);
          } else if (sourcesData.contexts) {
            onSources(sourcesData.contexts);
          }
          sourcesProcessed = true;
          buffer = rest || '';
        } catch (e) {
          continue;
        }
      }

      // Process content and related questions
      if (buffer.includes(RELATED_SPLIT)) {
        const [content, relatesStr] = buffer.split(RELATED_SPLIT);
        
        // Stream the content before related questions
        if (content) {
          onMarkdown(content
            .replace(/\[\[([cC])itation/g, "[citation")
            .replace(/[cC]itation:(\d+)]]/g, "citation:$1]")
            .replace(/\[\[([cC]itation:\d+)]](?!])/g, `[$1]`)
            .replace(/\[[cC]itation:(\d+)]/g, "[citation]($1)")
          );
        }

        // Process related questions if complete
        if (relatesStr && relatesStr.trim().startsWith('[') && relatesStr.trim().endsWith(']')) {
          try {
            const questions = relatesStr.trim()
              .slice(1, -1)
              .split(',')
              .map(q => q.trim().replace(/^["']|["']$/g, ''));
            
            const relates = questions
              .filter(q => q && !q.startsWith('提出的问题：'))
              .map(question => ({ question }));
            
            onRelates(relates);
            buffer = '';
          } catch (e) {
            buffer = relatesStr;
          }
        }
        continue;
      }

      // Stream regular content
      if (buffer) {
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep the last potentially incomplete line

        for (const line of lines) {
          if (!line.trim()) continue;
          
          try {
            const data = JSON.parse(line);
            if (data.content) {
              onMarkdown(data.content
                .replace(/\[\[([cC])itation/g, "[citation")
                .replace(/[cC]itation:(\d+)]]/g, "citation:$1]")
                .replace(/\[\[([cC]itation:\d+)]](?!])/g, `[$1]`)
                .replace(/\[[cC]itation:(\d+)]/g, "[citation]($1)")
              );
            }
          } catch (e) {
            // If not JSON, treat as raw content
            onMarkdown(line + '\n');
          }
        }
      }
    }
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        // Ignore abort errors as they are expected when navigating away
        return;
      }
      console.error("Error in parseStreaming:", error);
      onError?.(500);
    }
  } finally {
    try {
      controller.abort();
    } catch (e) {
      // Ignore abort errors
    }
  }
};
