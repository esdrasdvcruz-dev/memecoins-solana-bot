/*
  Warnings:

  - You are about to drop the column `coinbaseChargeId` on the `Order` table. All the data in the column will be lost.

*/
-- RedefineTables
PRAGMA defer_foreign_keys=ON;
PRAGMA foreign_keys=OFF;
CREATE TABLE "new_Order" (
    "id" TEXT NOT NULL PRIMARY KEY,
    "customerName" TEXT NOT NULL,
    "customerEmail" TEXT NOT NULL,
    "customerPhone" TEXT NOT NULL,
    "pickupTime" DATETIME NOT NULL,
    "notes" TEXT,
    "status" TEXT NOT NULL DEFAULT 'PENDING_PAYMENT',
    "paymentMethod" TEXT NOT NULL,
    "subtotalCents" INTEGER NOT NULL,
    "totalCents" INTEGER NOT NULL,
    "currency" TEXT NOT NULL DEFAULT 'MXN',
    "conektaOrderId" TEXT,
    "nowPaymentsInvoiceId" TEXT,
    "transferReference" TEXT,
    "createdAt" DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" DATETIME NOT NULL
);
INSERT INTO "new_Order" ("conektaOrderId", "createdAt", "currency", "customerEmail", "customerName", "customerPhone", "id", "notes", "paymentMethod", "pickupTime", "status", "subtotalCents", "totalCents", "transferReference", "updatedAt") SELECT "conektaOrderId", "createdAt", "currency", "customerEmail", "customerName", "customerPhone", "id", "notes", "paymentMethod", "pickupTime", "status", "subtotalCents", "totalCents", "transferReference", "updatedAt" FROM "Order";
DROP TABLE "Order";
ALTER TABLE "new_Order" RENAME TO "Order";
CREATE UNIQUE INDEX "Order_transferReference_key" ON "Order"("transferReference");
PRAGMA foreign_keys=ON;
PRAGMA defer_foreign_keys=OFF;
