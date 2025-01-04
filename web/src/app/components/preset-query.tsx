'use client';

import { getSearchUrl } from '@/app/utils/get-search-url';
import { nanoid } from 'nanoid';
import Link from 'next/link';
import React, { FC } from 'react';

interface Props {
  query: string;
}

export const PresetQuery: FC<Props> = ({ query }) => {
  const searchId = nanoid();

  return (
    <Link
      prefetch={false}
      title={query}
      href={getSearchUrl(encodeURIComponent(query), searchId)}
      className="border border-zinc-200/50 text-ellipsis overflow-hidden text-nowrap items-center rounded-lg bg-zinc-100 hover:bg-zinc-200/80 hover:text-zinc-950 px-2 py-1 text-xs font-medium text-zinc-600"
    >
      {query}
    </Link>
  );
};
