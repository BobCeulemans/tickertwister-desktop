// SPDX-License-Identifier: AGPL-3.0-only
// Copyright ©2026 Bob Ceulemans
export default function Fold({title,children,open=false}){return <details className="work-fold" open={open}><summary>{title}</summary><div className="fold-content">{children}</div></details>;}
