import { useTheme } from "@fiftyone/components";
import * as fos from "@fiftyone/state";
import { Field } from "@fiftyone/utilities";
import ExpandLess from "@mui/icons-material/ExpandLess";
import ExpandMore from "@mui/icons-material/ExpandMore";
import Collapse from "@mui/material/Collapse";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import { Resizable } from "re-resizable";
import React, { useState } from "react";
import { useRecoilCallback, useRecoilValue } from "recoil";
import { resizeHandle } from "./../Sidebar/Sidebar.module.css";
import { ACTIVE_FIELD } from "./utils";

const SidebarList: React.FC = () => {
  const theme = useTheme();
  const activeField = useRecoilValue(fos.activeColorField);

  const [width, setWidth] = useState(200);
  const stableGroup = [
    { paths: [ACTIVE_FIELD.global, ACTIVE_FIELD.json], name: "general" },
  ];
  const fieldGroups = useRecoilValue(
    fos.sidebarGroups({ modal: false, loading: false })
  ).filter((g) => g.name !== "tags");
  const groups = [...stableGroup, ...fieldGroups];
  const [groupOpen, setGroupOpen] = React.useState(
    new Array(groups.length).fill(true)
  );
  const handleGroupClick = (ev, idx) => {
    setGroupOpen((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const onSelectField = useRecoilCallback(
    ({ set, snapshot }) =>
      async (path: string) => {
        if ([ACTIVE_FIELD.global, ACTIVE_FIELD.json].includes(path)) {
          set(fos.activeColorField, path);
        } else {
          const field = await snapshot.getPromise(fos.field(path));
          set(fos.activeColorField, field);
        }
      },
    []
  );

  const getCurrentField = (activeField) => {
    if (activeField === ACTIVE_FIELD.global) return ACTIVE_FIELD.global;
    if (activeField === ACTIVE_FIELD.json) return ACTIVE_FIELD.json;
    return activeField?.path;
  };
  return (
    <Resizable
      size={{ height: "100%", width }}
      minWidth={200}
      maxWidth={600}
      enable={{
        top: false,
        right: true,
        left: false,
        bottom: false,
        topRight: false,
        bottomRight: false,
        bottomLeft: false,
        topLeft: false,
      }}
      onResizeStop={(e, direction, ref, { width: d }) => {
        setWidth(width + d);
        // reset sidebar width on double click
        if (e.detail === 2) setWidth(200);
      }}
      handleStyles={{
        ["right"]: { right: 0, width: 4 },
      }}
      handleClasses={{
        ["right"]: resizeHandle,
      }}
      style={{ overflow: "auto" }}
    >
      <List
        sx={{
          bgcolor: theme.background.level2,
          height: "100%",
          width: "100%",
          borderRight: `1px solid ${theme.background.level3}`,
        }}
        component="nav"
        aria-labelledby="nested-list-subheader"
      >
        {groups.map((group, index) => {
          return (
            <div key={`group-${group.name}`}>
              <ListItemButton
                onClick={(ev) => handleGroupClick(ev, index)}
                disableRipple
              >
                <ListItemText
                  primary={group.name?.toUpperCase()}
                  sx={{ fontFamily: "palanquin, sans-serif" }}
                />
                {groupOpen[index] ? <ExpandLess /> : <ExpandMore />}
              </ListItemButton>
              <Collapse in={groupOpen[index]} timeout="auto" unmountOnExit>
                <List component="div" disablePadding>
                  {group.paths.map((path, pathIdx) => (
                    <ListItemButton
                      sx={{ pl: 4, margin: "-0.25rem" }}
                      key={`menu-${pathIdx}`}
                      selected={path === getCurrentField(activeField)}
                      disableRipple
                    >
                      <ListItemText
                        primary={path}
                        onClick={() => onSelectField(path)}
                        sx={{ fontFamily: "palanquin, sans-serif" }}
                      />
                    </ListItemButton>
                  ))}
                </List>
              </Collapse>
            </div>
          );
        })}
      </List>
    </Resizable>
  );
};

export default SidebarList;