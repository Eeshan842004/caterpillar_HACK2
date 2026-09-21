import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Workspace } from '@/components/Workspace';

describe('Epic E-05: Operational Workspace UI', () => {
  describe('QA-E05-01: Asset Fleet Selection & Status Rendering', () => {
    it('renders all 4 fleet machines and highlights selected asset', () => {
      render(<Workspace />);

      expect(screen.getByText('336 Hydraulic Excavator')).toBeInTheDocument();
      expect(screen.getByText('745 Articulated Truck')).toBeInTheDocument();
      expect(screen.getByText('980 Wheel Loader')).toBeInTheDocument();
      expect(screen.getByText('963 Track Loader')).toBeInTheDocument();

      // Asset 336 has CRITICAL status
      expect(screen.getAllByText('CRITICAL').length).toBeGreaterThan(0);

      // Switch asset selection to 980 Wheel Loader
      fireEvent.click(screen.getByText('980 Wheel Loader'));
      expect(screen.getByText(/980 Wheel Loader \(CAT-980-WLD-1205\)/i)).toBeInTheDocument();
    });
  });

  describe('QA-E05-02: Telemetry & Faults Rendering', () => {
    it('displays active fault codes and emergency recommendation on hero asset', () => {
      render(<Workspace />);

      // Switch to hero asset 336
      fireEvent.click(screen.getByText('336 Hydraulic Excavator'));

      // Active DTC fault
      expect(screen.getByText('SPN 110 FMI 0')).toBeInTheDocument();
      expect(screen.getAllByText(/Engine Coolant Temperature/i).length).toBeGreaterThan(0);

      // Recommendation card
      expect(screen.getByText(/Emergency Coolant System Inspection Required/i)).toBeInTheDocument();
      expect(screen.getByText('94%')).toBeInTheDocument();
      expect(screen.getByText(/Review & Confirm Work Order/i)).toBeInTheDocument();
    });
  });

  describe('QA-E05-03: Human Confirmation Modal Flow', () => {
    it('opens safety confirmation modal and authorizes work order dispatch', () => {
      render(<Workspace />);

      fireEvent.click(screen.getByText('336 Hydraulic Excavator'));

      // Click review & confirm button
      const reviewButton = screen.getByText(/Review & Confirm Work Order/i);
      fireEvent.click(reviewButton);

      // Verify modal is displayed
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Human Authorization: Dispatch Work Order/i)).toBeInTheDocument();
      expect(screen.getByText(/SAFETY COMPLIANCE GATE/i)).toBeInTheDocument();

      // Authorize & Dispatch
      const authorizeButton = screen.getByText('Authorize & Dispatch Work Order');
      fireEvent.click(authorizeButton);

      // Modal closes
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

      // Work order appears in Dispatched list & audit log
      expect(screen.getByText(/Dispatched Work Orders \(1\)/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Emergency Coolant Circuit Repair/i).length).toBeGreaterThan(0);
    });
  });

  describe('QA-E05-04: Reset Demo Determinism in UI', () => {
    it('clears work orders and resets state upon clicking Reset Demo State', () => {
      render(<Workspace />);

      // Dispatch a work order first
      fireEvent.click(screen.getByText('336 Hydraulic Excavator'));
      fireEvent.click(screen.getByText(/Review & Confirm Work Order/i));
      fireEvent.click(screen.getByText('Authorize & Dispatch Work Order'));

      expect(screen.getByText(/Dispatched Work Orders \(1\)/i)).toBeInTheDocument();

      // Click Reset Demo State
      const resetButton = screen.getByRole('button', { name: /Reset Demo State/i });
      fireEvent.click(resetButton);

      // Verify reset initiated
      expect(screen.getByText(/Resetting.../i)).toBeInTheDocument();
    });
  });
});
