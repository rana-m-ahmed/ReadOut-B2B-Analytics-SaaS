"use client"

import * as React from "react"
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { Metric, LabelText } from "@/components/ui/typography"
import { ModalWrapper } from "@/components/ui/modal-wrapper"

export default function TokensDevPage() {
  const [isModalOpen, setIsModalOpen] = React.useState(false)

  return (
    <div className="min-h-screen p-8 bg-[var(--canvas)] space-y-12">
      <div className="space-y-4">
        <h1 className="text-2xl font-bold text-[var(--ink)]">Design System Primitives</h1>
        <p className="text-[var(--ink-secondary)]">Architectural Soft-Contrast validation</p>
      </div>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--ink)] border-b pb-2">Typography</h2>
        <div className="flex flex-col gap-4">
          <div className="flex flex-col">
            <LabelText>Total Revenue</LabelText>
            <Metric>$1,234,567.89</Metric>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--ink)] border-b pb-2">Button</h2>
        <div className="flex gap-4 items-center">
          <Button variant="default">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--ink)] border-b pb-2">Card</h2>
        <Card className="w-[350px]">
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
            <CardDescription>This is a subtle description</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-[var(--ink)]">Main card content goes here. The card should appear elevated with a float shadow and no harsh borders.</p>
          </CardContent>
          <CardFooter className="justify-between">
            <Button variant="ghost">Cancel</Button>
            <Button>Save</Button>
          </CardFooter>
        </Card>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--ink)] border-b pb-2">Tooltip</h2>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger render={<Button variant="outline" />}>
              Hover me
            </TooltipTrigger>
            <TooltipContent>
              <p>This is a tooltip</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--ink)] border-b pb-2">Skeleton</h2>
        <div className="flex items-center space-x-4">
          <Skeleton className="h-12 w-12 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-[250px]" />
            <Skeleton className="h-4 w-[200px]" />
          </div>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-[var(--ink)] border-b pb-2">Modal</h2>
        <Button onClick={() => setIsModalOpen(true)}>Open Modal</Button>
        <ModalWrapper isOpen={isModalOpen} onClose={() => setIsModalOpen(false)}>
          <div className="space-y-4">
            <h2 className="text-xl font-bold text-[var(--ink)]">Modal Title</h2>
            <p className="text-[var(--ink-secondary)]">The background canvas should be scaled down and blurred.</p>
            <Button onClick={() => setIsModalOpen(false)}>Close</Button>
          </div>
        </ModalWrapper>
      </section>
    </div>
  )
}
