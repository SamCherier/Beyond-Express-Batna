import React, { useState, useEffect, useCallback } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import Barcode from 'react-barcode';
import { Printer, ArrowLeft, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import api from '../api';
import './ProformaInvoice.css';

const fmt = (n) => new Intl.NumberFormat('fr-DZ', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);

const ProformaInvoicePage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchInvoice = useCallback(async () => {
    const ids = searchParams.get('orders');
    if (!ids) { setError('Aucune commande sélectionnée'); setLoading(false); return; }

    try {
      const orderIds = ids.split(',');
      const res = await api.post('/invoices/proforma/generate', {
        order_ids: orderIds,
        lieu: 'Batna',
      });
      setInvoice(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || 'Erreur lors de la génération');
    } finally {
      setLoading(false);
    }
  }, [searchParams]);

  useEffect(() => { fetchInvoice(); }, [fetchInvoice]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen bg-white">
      <Loader2 className="w-8 h-8 animate-spin text-[#E61E2A]" />
    </div>
  );

  if (error) return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white gap-4">
      <p className="text-red-600 text-sm">{error}</p>
      <Button variant="outline" onClick={() => navigate(-1)}>Retour</Button>
    </div>
  );

  if (!invoice) return null;

  return (
    <div className="min-h-screen bg-gray-100 py-6" data-testid="proforma-page">
      {/* Actions Bar */}
      <div className="proforma-actions max-w-[210mm] mx-auto px-6 no-print">
        <Button variant="outline" size="sm" onClick={() => navigate(-1)} data-testid="proforma-back-btn">
          <ArrowLeft className="w-4 h-4 mr-1" /> Retour
        </Button>
        <Button size="sm" onClick={() => window.print()} className="bg-[#E61E2A] text-white hover:bg-[#c5171f]" data-testid="proforma-print-btn">
          <Printer className="w-4 h-4 mr-1" /> Imprimer / PDF
        </Button>
      </div>

      {/* Invoice Body */}
      <div className="proforma-page shadow-lg" data-testid="proforma-body">
        {/* ── HEADER ── */}
        <div className="proforma-header">
          <div className="proforma-logo">
            <div className="proforma-logo-icon">B</div>
            <div className="proforma-logo-text">
              <h1>Beyond Express</h1>
              <p>Plateforme de Livraison Algérienne</p>
            </div>
          </div>

          <div className="proforma-title-block">
            <h2>Décharge de colis</h2>
            <p>Facture Proforma</p>
          </div>

          <div className="proforma-barcode" data-testid="proforma-barcode">
            <Barcode
              value={invoice.reference}
              width={1.2}
              height={40}
              fontSize={10}
              margin={0}
              displayValue={true}
            />
          </div>
        </div>

        {/* ── META ── */}
        <div className="proforma-meta">
          <div className="proforma-meta-item">
            <strong>Réf:</strong> {invoice.reference}
          </div>
          <div className="proforma-meta-item">
            <strong>{invoice.lieu}</strong> le {invoice.date}
          </div>
          <div className="proforma-meta-item">
            <strong>{invoice.order_count}</strong> colis
          </div>
        </div>

        {/* ── CLIENT INFO ── */}
        <div className="proforma-client" data-testid="proforma-client">
          <div className="proforma-client-title">Informations Client / Boutique</div>
          <div className="proforma-client-field">
            <span>Nom / Boutique</span>
            <strong>{invoice.client.name}</strong>
          </div>
          <div className="proforma-client-field">
            <span>Téléphone</span>
            {invoice.client.phone || '—'}
          </div>
          <div className="proforma-client-field">
            <span>E-mail</span>
            {invoice.client.email || '—'}
          </div>
          <div className="proforma-client-field">
            <span>Adresse</span>
            {invoice.client.address || '—'}
          </div>
        </div>

        {/* ── TABLE ── */}
        <table className="proforma-table" data-testid="proforma-table">
          <thead>
            <tr>
              <th style={{ width: '3%' }}>#</th>
              <th style={{ width: '11%' }}>Référence</th>
              <th style={{ width: '11%' }}>Article</th>
              <th style={{ width: '11%' }}>Destinataire</th>
              <th style={{ width: '9%' }}>Téléphone</th>
              <th style={{ width: '9%' }}>Wilaya</th>
              <th style={{ width: '9%' }}>Commune</th>
              <th style={{ width: '5%' }}>Poids</th>
              <th style={{ width: '9%' }}>Montant</th>
              <th style={{ width: '8%' }}>Livraison</th>
              <th style={{ width: '8%' }}>Prestation</th>
              <th style={{ width: '9%' }}>Net</th>
            </tr>
          </thead>
          <tbody>
            {invoice.items.map((item, i) => (
              <tr key={i}>
                <td>{i + 1}</td>
                <td className="col-ref">{item.reference}</td>
                <td className="col-text-left">{item.article}</td>
                <td className="col-text-left">{item.destinataire}</td>
                <td>{item.telephone}</td>
                <td>{item.wilaya}</td>
                <td>{item.commune}</td>
                <td>{item.poids} kg</td>
                <td className="col-amount">{fmt(item.montant)}</td>
                <td>{fmt(item.tarif_livraison)}</td>
                <td>{fmt(item.tarif_prestation)}</td>
                <td className="col-amount">{fmt(item.net)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* ── FOOTER ── */}
        <div className="proforma-footer" data-testid="proforma-footer">
          {/* Signature */}
          <div className="proforma-signature">
            <div className="proforma-signature-title">Signature Client</div>
            <div className="proforma-signature-line" />
            <div className="proforma-signature-label">Nom, Prénom et Signature</div>
          </div>

          {/* Totals */}
          <div className="proforma-totals" data-testid="proforma-totals">
            <div className="proforma-totals-row">
              <span>Total Montant</span>
              <span>{fmt(invoice.totals.montant)} DZD</span>
            </div>
            <div className="proforma-totals-row">
              <span>Frais de Livraison</span>
              <span>{fmt(invoice.totals.livraison)} DZD</span>
            </div>
            <div className="proforma-totals-row">
              <span>Frais de Prestation</span>
              <span>{fmt(invoice.totals.prestation)} DZD</span>
            </div>
            <div className="proforma-totals-row total-row">
              <span>NET A PAYER</span>
              <span>{fmt(invoice.totals.net)} DZD</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProformaInvoicePage;
