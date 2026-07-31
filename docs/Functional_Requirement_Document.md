# Functional Requirement Document (FRD)

## 1. Overview

This document defines the core functional requirements of My Hope Story, including user roles, features, and acceptance criteria.

## 2. User Roles

- Guest: browse content, search, view stories
- Registered User: comment, bookmark, follow, donate
- Entrepreneur: submit stories, manage profile, request mentorship
- Mentor: review stories, offer advice, connect with founders
- Investor: evaluate stories, connect with founders, support ideas
- Moderator: verify content, manage reviews, enforce policies
- Admin: platform configuration, analytics, compliance

## 3. User Registration and Authentication

- Email/password signup
- OAuth login: Google, LinkedIn
- Optional phone OTP verification
- Password reset flow
- Role-based access control

## 4. Entrepreneur Profile

- Profile fields: photo, bio, startup name, industry, location, website, socials
- Achievement highlights
- Visibility settings: public, private, anonymous

## 5. Story Submission

- Required fields: title, startup name, industry, problem, solution, timeline, failure reason, lessons learned, future plans
- Optional fields: funding history, revenue, team, supporting documents, multimedia
- Story categories: technology, healthcare, education, fintech, social impact, and others
- Submission wizard for structured storytelling

## 6. Content and Moderation Workflow

- AI pre-screening for spam, plagiarism, hate speech
- Moderator review queue for story verification
- Fact-checking support for funding claims
- Publish/reject/feedback statuses
- Revision requests and resubmission

## 7. Community Interaction

- Like, comment, share, bookmark
- Follow founders and story categories
- Discussion threads and Q&A
- Report content abuse

## 8. Search and Discovery

- Search by keyword, industry, country, failure reason, funding status, founder name
- Filters for story stage, category, verified status
- Recommendation engine: similar stories, mentors, investors
- Trending stories and editor’s picks

## 9. Funding and Support Modules

- Donation page with predefined amounts and custom donations
- Crowdfunding campaigns with goals, deadlines, rewards
- Investor interest form and direct connection requests
- Grant and incubator recommendation engine
- Startup revival program application

## 10. Notifications and Communication

- Email notifications for story status, comments, funding interest
- In-app notifications for mentorship invites, investor messages
- SMS or push notification support for critical updates

## 11. Privacy and Security

- Privacy settings for story visibility and financial data
- Anonymous publishing option
- Secure storage of documents and media
- GDPR and data protection compliance features

## 12. Analytics and Reporting

- Founder dashboard: story performance, engagement, funding activity
- Mentor and investor dashboards: recommendations, saved stories
- Admin analytics: user growth, content quality, moderation load

## 13. Acceptance Criteria

- Entrepreneurs can submit and edit structured stories.
- Moderators can review and publish or reject stories.
- Users can donate and express interest in support.
- Search returns relevant stories with filters.
- Recommendation engine surfaces related content.
- Privacy controls allow anonymous and hidden financial details.
