import React, { useState } from 'react';
import type { MortalityTable } from '../../types';
import TablesSubNavigation, { type TablesSubView } from './TablesSubNavigation';
import TablesAnalysisView from './tables/TablesAnalysisView';
import TablesManageView from './tables/TablesManageView';
import TablesAddView from './tables/TablesAddView';

interface TablesAnalysisTabProps {
  mortalityTables: MortalityTable[];
  loading: boolean;
}

const TablesAnalysisTab: React.FC<TablesAnalysisTabProps> = ({
  mortalityTables,
  loading
}) => {
  const [activeView, setActiveView] = useState<TablesSubView>('analysis');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Tábuas de Mortalidade
        </h1>
        <p className="text-gray-600">
          Visualize, compare e gerencie tábuas de mortalidade atuariais.
        </p>
      </div>

      {/* Sub-navegação */}
      <TablesSubNavigation
        activeView={activeView}
        onViewChange={setActiveView}
      />

      {/* Conteúdo baseado na view ativa */}
      {activeView === 'analysis' && <TablesAnalysisView />}
      {activeView === 'manage' && <TablesManageView />}
      {activeView === 'add' && <TablesAddView />}
    </div>
  );
};

export default TablesAnalysisTab;
