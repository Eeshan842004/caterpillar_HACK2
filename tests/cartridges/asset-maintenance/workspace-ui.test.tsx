import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { Workspace } from '@/cartridges/asset-maintenance/components/Workspace';
import { ReferenceTestClient } from './test-client';

const renderWorkspace = () => render(<Workspace client={new ReferenceTestClient()} />);

describe('Epic E-05: Operational Workspace UI', () => {
  describe('QA-E05-01: Asset Fleet Selection & Status Rendering', () => {
    it('renders all 4 fleet machines and highlights selected asset', async () => {
      renderWorkspace();

      expect(await screen.findByText('336 Hydraulic Excavator')).toBeInTheDocument();
      expect(screen.getByText('745 Articulated Truck')).toBeInTheDocument();
      expect(screen.getByText('980 Wheel Loader')).toBeInTheDocument();
      expect(screen.getByText('963 Track Loader')).toBeInTheDocument();
      expect(screen.getAllByText('CRITICAL').length).toBeGreaterThan(0);

      fireEvent.click(screen.getByText('980 Wheel Loader'));
      expect(
        await screen.findByText(/980 Wheel Loader \(CAT-980-WLD-1205\)/i)
      ).toBeInTheDocument();
    });
  });

  describe('QA-E05-02: Telemetry & Faults Rendering', () => {
    it('displays active fault codes and emergency recommendation on hero asset', async () => {
      renderWorkspace();

      expect(await screen.findByText('336 Hydraulic Excavator')).toBeInTheDocument();
      expect(await screen.findByText('SPN 110 FMI 0')).toBeInTheDocument();
      expect(screen.getAllByText(/Engine Coolant Temperature/i).length).toBeGreaterThan(0);
      expect(
        screen.getByText(/Emergency Coolant System Inspection Required/i)
      ).toBeInTheDocument();
      expect(screen.getByText('94%')).toBeInTheDocument();
      expect(screen.getByText(/Review & Confirm Work Order/i)).toBeInTheDocument();
    });
  });

  describe('QA-E05-03: Human Confirmation Modal Flow', () => {
    it('dispatches through the shared client and refreshes server-backed lists', async () => {
      renderWorkspace();

      fireEvent.click(await screen.findByText(/Review & Confirm Work Order/i));
      expect(screen.getByRole('dialog')).toBeInTheDocument();
      expect(screen.getByText(/Human Authorization: Dispatch Work Order/i)).toBeInTheDocument();

      fireEvent.click(screen.getByText('Authorize & Dispatch Work Order'));

      await waitFor(() => {
        expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
      });
      expect(await screen.findByText(/Dispatched Work Orders \(1\)/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Emergency Coolant Circuit Repair/i).length).toBeGreaterThan(0);
    });
  });

  describe('QA-E05-04: Reset Demo Determinism in UI', () => {
    it('clears server-backed work orders when reset is requested', async () => {
      renderWorkspace();

      fireEvent.click(await screen.findByText(/Review & Confirm Work Order/i));
      fireEvent.click(screen.getByText('Authorize & Dispatch Work Order'));
      expect(await screen.findByText(/Dispatched Work Orders \(1\)/i)).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /Reset Demo State/i }));

      expect(await screen.findByText(/Dispatched Work Orders \(0\)/i)).toBeInTheDocument();
    });
  });
});
