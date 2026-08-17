import * as React from "react";

import { usePermissions } from "@/core/rbac/permissions-provider";
import { NAV_GROUPS, type NavGroup } from "@/core/rbac/nav-config";

/**
 * The authorized menu: `NAV_GROUPS` filtered by the User's real, resolved
 * permissions. An item with `requiredPermissions: []` (Dashboard) is always
 * visible to any authenticated User; every other item needs at least one of
 * its listed codes. Groups that end up with zero visible items are dropped
 * entirely rather than rendered as an empty section header.
 */
export function useAuthorizedNav(): NavGroup[] {
  const { hasAnyPermission } = usePermissions();

  return React.useMemo(() => {
    return NAV_GROUPS.map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => item.requiredPermissions.length === 0 || hasAnyPermission(item.requiredPermissions)
      ),
    })).filter((group) => group.items.length > 0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasAnyPermission]);
}
