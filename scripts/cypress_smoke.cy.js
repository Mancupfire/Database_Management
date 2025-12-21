/// <reference types="cypress" />

/**
 * Minimal Cypress smoke to cover login + dashboards render.
 * Requires frontend at BASE_URL (default http://localhost:8080) and backend at BACKEND_URL.
 */
const BASE_URL = Cypress.env("BASE_URL") || "http://localhost:8080";
const BACKEND_URL = Cypress.env("BACKEND_URL") || "http://localhost:5000";

describe("MoneyMinder UI/API smoke", () => {
  it("shows landing and performs API login", () => {
    cy.visit(BASE_URL);
    cy.contains("MoneyMinder");

    cy.request("POST", `${BACKEND_URL}/api/auth/login`, {
      email: "john.doe@example.com",
      password: "Demo@2024",
    }).then((resp) => {
      expect(resp.status).to.eq(200);
      expect(resp.body).to.have.property("token");
    });
  });
});
