from __future__ import annotations

from pydantic import BaseModel, Field


class CompanyProfile(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    industry: str = Field(default="", max_length=100)
    target_audience: str = Field(default="", max_length=500)
    product: str = Field(default="", max_length=2000)
    website: str = Field(default="", max_length=500)
    stage: str = Field(default="pre-launch", pattern=r"^(pre-launch|launched|growth)$")
    key_features: list[str] = Field(default_factory=list)
    differentiators: str = Field(default="", max_length=2000)
    jurisdictions: list[str] = Field(default_factory=lambda: ["US"])

    def to_context_string(self) -> str:
        """Render the company profile as a context block for agent prompts."""
        lines = [
            f"Company: {self.name}",
            f"Description: {self.description}",
        ]
        if self.industry:
            lines.append(f"Industry: {self.industry}")
        if self.target_audience:
            lines.append(f"Target audience: {self.target_audience}")
        if self.product:
            lines.append(f"Product/Service: {self.product}")
        if self.website:
            lines.append(f"Website: {self.website}")
        lines.append(f"Stage: {self.stage}")
        if self.key_features:
            lines.append(f"Key features: {', '.join(self.key_features)}")
        if self.differentiators:
            lines.append(f"Differentiators: {self.differentiators}")
        if self.jurisdictions:
            lines.append(f"Jurisdictions: {', '.join(self.jurisdictions)}")
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """Render the company profile as a Markdown document."""
        sections = [
            f"# {self.name}",
            "",
            f"> {self.description}",
            "",
        ]
        if self.industry:
            sections.append(f"**Industry:** {self.industry}  ")
        if self.target_audience:
            sections.append(f"**Target Audience:** {self.target_audience}  ")
        if self.website:
            sections.append(f"**Website:** {self.website}  ")
        sections.append(f"**Stage:** {self.stage}  ")
        if self.jurisdictions:
            sections.append(f"**Jurisdictions:** {', '.join(self.jurisdictions)}  ")
        sections.append("")

        if self.product:
            sections.extend(["## Product / Service", "", self.product, ""])
        if self.key_features:
            sections.append("## Key Features")
            sections.append("")
            for feat in self.key_features:
                sections.append(f"- {feat}")
            sections.append("")
        if self.differentiators:
            sections.extend(["## Differentiators", "", self.differentiators, ""])

        return "\n".join(sections)
