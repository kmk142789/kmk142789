# Verification Profile Settings Guide

This page summarizes the current layout and purpose of the verification profile detail view.
It captures the key controls and values visible in the UI so product, design, and QA teams
share a common reference when reviewing changes.

## Overview
- **Live badge** at the top indicates the profile status.
- **Toggle Sidebar** control collapses or expands the navigation for focused editing.
- **Back to Verification Profiles** link returns to the list view.

## Profile Header
- **Profile name:** `Echo` appears twice—once as the page title and again as the profile label.
- **Profile ID:** `06b831b9-df84-445c-b789-6c5e5f308755` with a "Copy Verification Profile ID" helper.
- **Counters:**
  - Enabled Providers: `1`
  - Approved Providers: `0`
  - Sessions Created: `1`

## Branding
- **Logo upload** block with a 512×512 px recommendation and preview placeholder.
- **Primary color** shows `#006BE5`, matching Trinsic's interface.
- **Domain selector** defaults to `verify.trinsic.id`, with guidance to add custom domains
  via the Domains page.

## Privacy
- Toggle labeled "When enabled, verification data is encrypted so that even Trinsic cannot
  access it at rest." Use **Reset** and **Save Changes** controls to manage updates.

## Providers
- Section title: "Verification Profile Providers" with an "Add Providers" action and search
  input for filtering by name or ID.
- Table columns: Provider, Enabled, Approved, Configuration, Actions.
- Current entry: **Austrian Handy-signatur** (`a-at-handy-signatur-login`) shows as Enabled,
  Approved, and Unlicensed under the Trinsic namespace.

Use this checklist when validating frontend changes or backend payloads that populate the
verification profile screen to ensure all expected elements remain present and correctly
labeled.
