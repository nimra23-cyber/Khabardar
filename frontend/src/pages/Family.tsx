import { useTranslation } from "react-i18next";

import { UnavailableState } from "../components/UnavailableState";

export default function Family() {
  const { t } = useTranslation();
  return (
    <div data-testid="page-family">
      <UnavailableState title={t("nav.family")} variant="scope-b" />
    </div>
  );
}
