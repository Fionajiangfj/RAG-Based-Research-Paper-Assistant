import { Box, Text, VStack } from '@chakra-ui/react';
import { SourceNode } from '../types';

interface SourceCitationProps {
  node: SourceNode;
}

export const SourceCitation = ({ node }: SourceCitationProps) => {
  return (
    <Box p={4} borderWidth="1px" borderRadius="md" bg="gray.50">
      <VStack align="stretch" spacing={2}>
        <Text>{node.text}</Text>
        {node.score && (
          <Text fontSize="sm" color="gray.600">
            Relevance Score: {node.score.toFixed(2)}
          </Text>
        )}
        {node.doc_id && (
          <Text fontSize="sm" color="gray.600">
            Document ID: {node.doc_id}
          </Text>
        )}
      </VStack>
    </Box>
  );
};
