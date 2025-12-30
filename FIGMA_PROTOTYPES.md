# LibreWork - Figma Design Specification

This document serves as a blueprint for creating the high-fidelity prototypes in Figma. It aligns with the Next.js frontend structure and TailwindCSS styling.

## 1. Design System

### 🎨 Color Palette
Based on the `tailwind.config.ts`:

**Primary (Brand)**
- `Primary-500` (#F9AB18): Main buttons, active states, brand accents
- `Primary-600` (#F8A015): Hover states
- `Primary-100` (#FDE4B8): Light backgrounds, subtle highlights

**Neutral**
- `Gray-900` (#111827): Headings, main text
- `Gray-700` (#374151): Body text
- `Gray-500` (#6B7280): Secondary text, icons
- `Gray-200` (#E5E7EB): Borders, dividers
- `Gray-50` (#F9FAFB): Page backgrounds

**Status**
- `Success` (#10B981): Available, Confirmed, Checked-in
- `Warning` (#F59E0B): Pending, Low availability
- `Error` (#EF4444): Cancelled, Error states

### 🔤 Typography
Font Family: **Inter** (Google Fonts)

| Style | Weight | Size (px) | Line Height | Usage |
|-------|--------|-----------|-------------|-------|
| H1 | Bold (700) | 48 | 1.2 | Hero Headings |
| H2 | Bold (700) | 30 | 1.3 | Section Titles |
| H3 | SemiBold (600) | 24 | 1.4 | Card Titles |
| Body L | Regular (400) | 18 | 1.5 | Intro text |
| Body M | Regular (400) | 16 | 1.5 | Standard text |
| Small | Medium (500) | 14 | 1.5 | Metadata, Labels |
| Tiny | Medium (500) | 12 | 1.5 | Tags, Badges |

### 📐 Grid & Spacing
- **Container**: Max-width 1280px, centered
- **Columns**: 12-column grid, 24px gutter
- **Spacing Unit**: 4px (Base unit). Common spacers: 16px, 24px, 32px, 48px, 64px.

---

## 2. Component Library

### Buttons
1.  **Primary Button**:
    *   Fill: `Primary-500`
    *   Text: White, Medium weight
    *   Radius: 8px (Rounded-lg)
    *   Padding: 12px 24px
2.  **Secondary Button**:
    *   Fill: `Gray-100`
    *   Text: `Gray-900`
    *   Radius: 8px
3.  **Ghost Button**:
    *   Fill: Transparent
    *   Text: `Gray-700` (Hover: `Primary-500`)

### Cards
*   **Establishment Card**:
    *   Image aspect ratio: 16:9
    *   Content padding: 16px
    *   Shadow: `shadow-sm` (Hover: `shadow-md`)
    *   Radius: 12px
*   **Reservation Card**:
    *   Layout: Horizontal row
    *   Left border: Status color indicator (4px wide)
    *   Background: White

### Inputs
*   **Text Field**:
    *   Border: 1px solid `Gray-300`
    *   Radius: 8px
    *   Height: 48px
    *   Focus: Ring 2px `Primary-500`

### Navigation
*   **Navbar**: Sticky top, white bg, border-bottom `Gray-200`. Logo left, Links right, User menu far right.
*   **Mobile Nav**: Hamburger menu expanding to full-screen list.

---

## 3. Screen Layouts (Prototypes)

### 🏠 1. Home Page (Landing)
**Hero Section**
*   Background: Gradient `Primary-50` to `Primary-100`
*   Center: Large H1 "Find Your Perfect Work Space"
*   Subtext: "Reserve spaces in cafes, libraries, and coworking areas."
*   CTAs: "Explore Spaces" (Primary), "Get Started" (Secondary)

**Features Grid**
*   3 Columns
*   Icons: MapPin, Clock, Coffee (Lucide style)
*   Title + Short description centered

**Recent/Featured Venues**
*   H2: "Popular Near You"
*   Horizontal scroll or grid of 3 Establishment Cards.

### 🔍 2. Explore / Search Page
**Filters Bar (Top)**
*   Inputs: "City/Location", "Category" (Dropdown), "Date/Time"
*   Toggle: "Show Map"

**Results Area**
*   **Left (List)**: Vertical stack of Establishment Cards. Each card shows:
    *   Thumbnail Image
    *   Name (H3)
    *   Category Badge (e.g., "Cafe" in Blue pill)
    *   Distance ("2.5 km away")
    *   Amenities icons (Wifi, Power)
*   **Right (Map)**: Map view with pins (Optional for MVP prototype).

### 🏢 3. Establishment Details
**Header**
*   Full-width hero image gallery (Grid of 1 main + 4 small).

**Content (2 Columns)**
*   **Left (70%)**:
    *   Title (H1), Rating (Star icon + "4.8"), Address.
    *   Description text.
    *   Amenities list (Grid of icons + labels).
    *   Reviews section.
*   **Right (30%) - Sticky Booking Card**:
    *   "Select a Space" dropdown (Table, Room).
    *   "Select Date & Time" picker.
    *   "Check Availability" button.
    *   Cost summary: "Total: 3 Credits".
    *   "Confirm Reservation" (Primary Button).

### 🎫 4. User Dashboard
**Stats Row**
*   3 Cards: "Active Reservations", "Credits Remaining", "Total Reviews".

**My Reservations (Tabs)**
*   Tabs: Upcoming | Past | Cancelled
*   List of Reservation Cards:
    *   Date/Time prominent.
    *   Venue Name & Space Name.
    *   Status Badge (Confirmed - Green).
    *   Action Buttons: "Get QR Code/Code", "Cancel".

### 📱 5. QR Code Modal (Overlay)
*   Appears when clicking "Get Code" on reservation.
*   Dimmed background.
*   White card centered.
*   Large QR Code image.
*   6-digit alphanumeric code below (e.g., "A7-B2-99").
*   "Close" button.

### 👮 6. Owner Dashboard (Management)
**Overview**
*   Graph: Reservations per day.
*   Quick Actions: "Scan QR", "Add Space".

**Scanner View (Mobile)**
*   Camera viewport mockup.
*   Overlay frame.
*   Bottom sheet: "Manual Entry" input field.

**Validation Success Screen**
*   Green checkmark animation.
*   Text: "Check-in Successful!".
*   User Name: "John Doe".
*   Space: "Table 4".
*   Time: "14:00 - 16:00".

---

## 4. User Flows

### Flow A: Booking a Space
1.  **Home** -> Click "Explore"
2.  **Search** -> Filter by "Cafe" -> Click "Café Central" card
3.  **Details** -> Select "Table 1", "Tomorrow 10am" -> Click "Confirm"
4.  **Confirmation Modal** -> "Success! You used 2 credits."
5.  **Dashboard** -> View new reservation ticket.

### Flow B: Check-in (Owner)
1.  **Owner Dash** -> Click "Scan QR"
2.  **Scanner** -> Simulate scan
3.  **Success Screen** -> "Reservation Validated" -> Click "Done"

