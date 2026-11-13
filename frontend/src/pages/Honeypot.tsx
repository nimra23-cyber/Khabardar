import { useTranslation } from "react-i18next";

import { UnavailableState } from "../components/UnavailableState";

export default function Honeypot() {
  const { t } = useTranslation();
  return (
    <div data-testid="page-honeypot">
      <UnavailableState title={t("nav.honeypot")} variant="scope-b" />
    </div>
  );
}
