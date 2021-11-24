import React, { useLayoutEffect, useMemo, useState } from "react";
import { useRecoilState, useRecoilValue } from "recoil";
import { Check, Visibility } from "@material-ui/icons";

import * as aggregationAtoms from "../../recoil/aggregations";
import * as filterAtoms from "../../recoil/filters";
import * as schemaAtoms from "../../recoil/schema";

import { MatchEye, Pills } from "./utils";
import { PathEntry, TextEntry } from "./Entries";
import {
  EMBEDDED_DOCUMENT_FIELD,
  LABELS_PATH,
  LABEL_DOC_TYPES,
  withPath,
} from "../../recoil/constants";
import { GroupHeader } from "./Sidebar";

const LabelTagsCell = React.memo(({ modal }: { modal: boolean }) => {
  const [expanded, setExpanded] = useState(true);
  const embeddedDocType = useMemo(
    () => withPath(LABELS_PATH, LABEL_DOC_TYPES),
    []
  );
  const tags = useRecoilValue(
    aggregationAtoms.cumulativeValues({
      extended: false,
      modal,
      path: "tags",
      ftype: EMBEDDED_DOCUMENT_FIELD,
      embeddedDocType,
    })
  );

  const title = `label tags`;
  const allTags = useRecoilValue(
    aggregationAtoms.cumulativeValues({
      extended: false,
      modal: false,
      path: "tags",
      ftype: EMBEDDED_DOCUMENT_FIELD,
      embeddedDocType,
    })
  );
  const [activeTags, setActiveTags] = useRecoilState(
    schemaAtoms.activeLabelTags(modal)
  );
  const [matchedTags, setMatchedTags] = useRecoilState(
    filterAtoms.matchedTags({ modal, key: "label" })
  );
  useLayoutEffect(() => {
    const newMatches = new Set<string>();
    matchedTags.forEach((tag) => {
      tags.includes(tag) && newMatches.add(tag);
    });

    newMatches.size !== matchedTags.size && setMatchedTags(newMatches);
  }, [matchedTags, allTags]);

  return (
    <>
      <GroupHeader
        title={title}
        expanded={expanded}
        onClick={() => setExpanded(!expanded)}
        style={{ marginBottom: 4 }}
      >
        <span>{title}</span>
        <Pills
          entries={[
            {
              icon: Check,
              title: "Clear displayed",
              onClick: () => setActiveTags([]),
              count: activeTags.length,
            },
            {
              icon: Visibility,
              title: "Clear matched",
              count: matchedTags.size,
              onClick: () => setMatchedTags(new Set()),
            },
          ]
            .filter(({ count }) => count > 0)
            .map(({ count, ...rest }) => ({
              ...rest,
              text: count.toLocaleString(),
            }))}
        />
      </GroupHeader>
      {expanded
        ? tags &&
          (tags.length ? (
            tags.map((tag) => (
              <PathEntry
                path={tag}
                modal={modal}
                ftype={EMBEDDED_DOCUMENT_FIELD}
                embeddedDocType={embeddedDocType}
                name={tag}
                disabled={false}
                key={tag}
                style={{ marginBottom: 4 }}
                pills={
                  <MatchEye
                    matched={matchedTags}
                    elementsName={"samples"}
                    name={tag}
                    onClick={() => {
                      const newMatch = new Set(matchedTags);
                      if (matchedTags.has(tag)) {
                        newMatch.delete(tag);
                      } else {
                        newMatch.add(tag);
                      }
                      setMatchedTags(newMatch);
                    }}
                  />
                }
              />
            ))
          ) : (
            <TextEntry text={"No label tags"} />
          ))
        : null}
    </>
  );
});

export default LabelTagsCell;
