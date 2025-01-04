import { Relate } from "@/app/interfaces/relate";
import { Source } from "@/app/interfaces/source";

// Get the base URL for API calls
const getBaseUrl = () => process.env.NEXT_PUBLIC_API_URL || '';

const getSearchUrl = () => `${getBaseUrl()}/search`;
const getGenerateUrl = () => `${getBaseUrl()}/generate`;
const getRelatedUrl = () => `${getBaseUrl()}/related`;

export const parseStreaming = async (
  controller: AbortController,
  query: string,
  search_uuid: string,
  onSources: (value: Source[]) => void,
  onMarkdown: (value: string | ((prev: string) => string)) => void,
  onRelates: (value: Relate[]) => void,
  onError?: (status: number) => void,
) => {
  const decoder = new TextDecoder();

  try {
    // 1. First call search API to get contexts
    const searchResponse = await fetch(getSearchUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        search_uuid,
      }),
      signal: controller.signal,
    });

    if (!searchResponse.ok) {
      onError?.(searchResponse.status);
      return;
    }

    const contexts = await searchResponse.json();
    onSources(contexts);

    // 2. Then call generate API to get streaming answer
    const generateResponse = await fetch(getGenerateUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        search_uuid,
        contexts,
      }),
      signal: controller.signal,
    });

    if (!generateResponse.ok) {
      onError?.(generateResponse.status);
      return;
    }

    const reader = generateResponse.body?.getReader();
    if (!reader) {
      throw new Error("No reader available");
    }

    // Process streaming response
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      
      // 追加模式，对整个文本进行格式化处理
      onMarkdown(prev => {
        const fullText = prev + chunk;
        return fullText
          .replace(/\[\[([cC])itation/g, "[citation")
          .replace(/[cC]itation:(\d+)]]/g, "citation:$1]")
          .replace(/\[\[([cC]itation:\d+)]](?!])/g, `[$1]`)
          .replace(/【citation:(\d+)】/g, "[citation]($1)")
          .replace(/\[[cC]itation:(\d+)]/g, "[citation]($1)");
      });
    }

    // 3. Finally call related API to get related questions
    const relatedResponse = await fetch(getRelatedUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        search_uuid,
        contexts,
      }),
      signal: controller.signal,
    });

    if (!relatedResponse.ok) {
      onError?.(relatedResponse.status);
      return;
    }

    const questions = await relatedResponse.json();
    const relates = questions.map((question: string) => ({ question }));
    onRelates(relates);

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
